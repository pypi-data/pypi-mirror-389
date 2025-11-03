from math import ceil
from numpy import where, round, full
from openfisca_core.model_api import min_, Variable, YEAR

from openfisca_france_dotations_locales.entities import Commune, Etat
from openfisca_france_dotations_locales.variables.base import safe_divide


# src : https://git.leximpact.dev/leximpact/simulateur-dotations-communes/openfisca-france-dotations-locales/-/blob/4.10.0/openfisca_france_dotations_locales/variables/dotation_solidarite_rurale_fractions/bourg_centre.py?ref_type=tags#L395
class dsr_montant_garantie_non_eligible_fraction_bourg_centre(Variable):
    value_type = float
    entity = Commune
    definition_period = YEAR
    label = "Garantie de sortie DSR fraction bourg-centre:\
        Montant garanti aux communes nouvellement inéligibles au titre de la fraction bourg-centre de la dotation de solidarité rurale"
    reference = "https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000036433099&cidTexte=LEGITEXT000006070633"
    documentation = '''Lorsqu'une commune cesse de remplir les conditions requises pour
        bénéficier de cette fraction de la dotation de solidarité rurale, cette
        commune perçoit, à titre de garantie non renouvelable, une attribution
        égale à la moitié de celle qu'elle a perçue l'année précédente.'''

    # AVANT PLF :
    # * sortie d'éligibilité fraction BC => garantie non renouvelable à (montant précédent / 2)
    # * dérogation si sortie éligibilité BC en 2017
    #   attribuable au plafonnement de population (src : 5 derniers alinéas même article)
    #   => garantie de sortie en 2018 == 100% montant précédent
    # * sortie d'éligibilité BC en 2012 =>
    #   garantie 2012 == 90% montant précédent donc 2011
    #   garantie 2013 == 75% montant 2011
    #   garantie 2014 == 50% montant 2011
    #
    # AU PLF 2026 :
    # sortie d'éligibilité fraction BC en 2026+
    # alors, par exemple si 2026 première année de sortie, (donc 2025 montant dernière année d'attribution)
    # garantie sur 2 années :
    #   garantie N 2026 == 75% montant 2025
    #   garantie N+1 2027 == 50% montant 2025
    # et on ne parle plus des sorties en 2012 et 2017.

    def formula_2025(commune, period, parameters):
        dsr_eligible_fraction_bourg_centre = commune("dsr_eligible_fraction_bourg_centre", period)
        montant_an_precedent = commune("dsr_montant_eligible_fraction_bourg_centre", period.last_year)
        part_garantie = 0.75  # TODO extraire en paramètre
        # TODO ajouter une variable de date de ou d'âge depuis sortie d'éligibilité
        # pour pouvoir modéliser "garantie N+1 2027 == 50% montant 2025"
        return (~dsr_eligible_fraction_bourg_centre) * montant_an_precedent * part_garantie

    def formula(commune, period, parameters):
        dsr_eligible_fraction_bourg_centre = commune("dsr_eligible_fraction_bourg_centre", period)
        montant_an_precedent = commune("dsr_montant_eligible_fraction_bourg_centre", period.last_year)
        part_garantie = 0.5  # TODO extraire en paramètre
        return (~dsr_eligible_fraction_bourg_centre) * montant_an_precedent * part_garantie


# src : https://git.leximpact.dev/leximpact/simulateur-dotations-communes/openfisca-france-dotations-locales/-/blob/4.10.0/openfisca_france_dotations_locales/variables/dotation_solidarite_rurale_fractions/cible.py?ref_type=tags#L7
class indice_synthetique_dsr_cible(Variable):
    value_type = float
    entity = Commune
    label = "Score pour classement DSR fraction cible (indice synthétique)"
    definition_period = YEAR
    reference = [
        'Code général des collectivités territoriales - Article L2334-22-1',
        'https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000037994647&cidTexte=LEGITEXT000006070633',
        "http://www.dotations-dgcl.interieur.gouv.fr/consultation/documentAffichage.php?id=94"
    ]

    def formula_2025(commune, period, parameters):
        # AVANT PLF :
        # Revenus :
        #   TODO vérifier les inputs de revenus sont peut-être déjà sur 3ans en 2025
        #   et du fait de la réforme qui décale de 1 année dans le passé, ils seraient à jour pour 2026
        #
        # AU PLF 2026 :
        # Revenus :
        #   TODO vérifier nature revenu_par_habitant : RFR dans le texte
        #   mais imposable dans le libellé de revenu_total
        #
        # Fait : mini refactorisation du code pour faire apparaître a) et b) de la loi
        population_dgf = commune("population_dgf", period)

        # TODO vérifier la période prise en compte pour l'input revenu_par_habitant
        # attendu PLF 2026 :
        # le revenu fiscal de référence de l’antépénultième année et des deux années précédentes.
        revenu_par_habitant = commune("revenu_par_habitant", period)
        revenu_par_habitant_strate = commune("revenu_par_habitant_moyen", period)
        potentiel_financier_par_habitant = commune("potentiel_financier_par_habitant", period)
        potentiel_financier_par_habitant_strate = commune("potentiel_financier_par_habitant_moyen", period)
        dsr_eligible_fraction_bourg_centre = commune("dsr_eligible_fraction_bourg_centre", period)
        dsr_eligible_fraction_perequation = commune("dsr_eligible_fraction_perequation", period)

        limite_population = parameters(period).dotation_solidarite_rurale.seuil_nombre_habitants
        parametres_poids = parameters(period).dotation_solidarite_rurale.cible.eligibilite.indice_synthetique
        poids_revenu = parametres_poids.poids_revenu
        poids_pot_fin = parametres_poids.poids_potentiel_financier

        # a) de l'article 2334-22-1
        rapport_potentiel_financier = safe_divide(potentiel_financier_par_habitant_strate, potentiel_financier_par_habitant, 0)

        # b) de l'article 2334-22-1
        rapport_revenu_par_habitant = safe_divide(revenu_par_habitant_strate, revenu_par_habitant, 0)

        return ((population_dgf < limite_population)
                * (dsr_eligible_fraction_bourg_centre | dsr_eligible_fraction_perequation)
                * (poids_pot_fin * rapport_potentiel_financier
                   + poids_revenu * rapport_revenu_par_habitant)
                )

    def formula(commune, period, parameters):
        # Cet indice synthétique est fonction :
        # a) Du rapport entre
        #    le potentiel financier par habitant moyen des communes appartenant au même groupe démographique
        #    et le potentiel financier par habitant de la commune ;
        # b) Du rapport entre
        #    la moyenne sur trois ans du revenu par habitant moyen des communes appartenant au même groupe démographique
        #    et la moyenne sur trois ans du revenu par habitant de la commune.
        #    Les revenus pris en considération sont les trois derniers revenus fiscaux de référence connus.

        population_dgf = commune("population_dgf", period)

        # TODO vérifier la période prise en compte pour l'input revenu_par_habitant
        # attendu trois derniers revenus fiscaux de référence connus
        revenu_par_habitant = commune("revenu_par_habitant", period)
        revenu_par_habitant_strate = commune("revenu_par_habitant_moyen", period)
        potentiel_financier_par_habitant = commune("potentiel_financier_par_habitant", period)
        potentiel_financier_par_habitant_strate = commune("potentiel_financier_par_habitant_moyen", period)
        dsr_eligible_fraction_bourg_centre = commune("dsr_eligible_fraction_bourg_centre", period)
        dsr_eligible_fraction_perequation = commune("dsr_eligible_fraction_perequation", period)

        limite_population = parameters(period).dotation_solidarite_rurale.seuil_nombre_habitants
        parametres_poids = parameters(period).dotation_solidarite_rurale.cible.eligibilite.indice_synthetique
        poids_revenu = parametres_poids.poids_revenu
        poids_pot_fin = parametres_poids.poids_potentiel_financier

        return ((population_dgf < limite_population)
                * (dsr_eligible_fraction_bourg_centre | dsr_eligible_fraction_perequation)
                * (poids_pot_fin * safe_divide(potentiel_financier_par_habitant_strate, potentiel_financier_par_habitant, 0)
                   + poids_revenu * safe_divide(revenu_par_habitant_strate, revenu_par_habitant, 0))
                )


# src : https://git.leximpact.dev/leximpact/simulateur-dotations-communes/openfisca-france-dotations-locales/-/blob/4.10.0/openfisca_france_dotations_locales/variables/dotation_solidarite_rurale_fractions/cible.py?ref_type=tags#L484
class dsr_montant_garantie_non_eligible_fraction_cible(Variable):
    value_type = float
    entity = Commune
    definition_period = YEAR
    label = "Garantie de sortie DSR fraction cible:\
        Montant garanti aux communes nouvellement inéligibles au titre de la fraction cible de la dotation de solidarité rurale"
    reference = "https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000037994647&cidTexte=LEGITEXT000006070633"
    documentation = '''Lorsqu'une commune cesse de remplir les conditions requises pour
        bénéficier de cette fraction de la dotation de solidarité rurale, cette
        commune perçoit, à titre de garantie non renouvelable, une attribution
        égale à la moitié de celle qu'elle a perçue l'année précédente.'''

    def formula_2025(commune, period, parameters):
        # AVANT PLF :
        # Garantie :
        #   sortie d'éligibilité fraction cible => garantie non renouvelable à (montant précédent / 2)
        #
        # AU PLF 2026 :
        # Garantie :
        #  sortie d'éligibilité fraction cible => fraction cible en 2026+
        #  alors, par exemple si 2026 première année de sortie (donc 2025 montant dernière année d'attribution),
        #  garantie sur 2 années :
        #    garantie N 2026 == 75% montant 2025
        #    garantie N+1 2027 == 50% montant 2025
        dsr_eligible_fraction_cible = commune("dsr_eligible_fraction_cible", period)
        montant_an_precedent = commune("dsr_montant_hors_garanties_fraction_cible", period.last_year)
        ratio_garantie = 0.75
        return (~dsr_eligible_fraction_cible) * montant_an_precedent * ratio_garantie

    def formula(commune, period, parameters):
        dsr_eligible_fraction_cible = commune("dsr_eligible_fraction_cible", period)
        montant_an_precedent = commune("dsr_montant_hors_garanties_fraction_cible", period.last_year)
        ratio_garantie = parameters(period).dotation_solidarite_rurale.cible.attribution.ratio_garantie  # 0.5
        return (~dsr_eligible_fraction_cible) * montant_an_precedent * ratio_garantie


class dsu_montant_eligible(Variable):
    value_type = float
    entity = Commune
    definition_period = YEAR
    label = "DSU au titre de l'éligibilité:\
        Montant total reçu par la commune au titre de son éligibilité à la DSU (incluant part spontanée et augmentation)"
    reference = "https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000033814543&cidTexte=LEGITEXT000006070633"

    # suppression du facteur ZFU (zones franches urbaines)
    # et avant PLF : recensement de population dans les zones existant au 1er janvier 2014
    # nouveau recensement non spécifié ; le plus récent ?
    def formula_2025(commune, period, parameters):
        dsu_montant_total = commune('dsu_montant_total', period)
        dsu_an_precedent = commune('dsu_montant_total', period.last_year)
        montants_an_precedent = commune('dsu_montant_eligible', period.last_year)
        dsu_eligible = commune('dsu_eligible', period)
        total_a_distribuer = commune('dsu_montant_total_eligibles', period)
        rang_indice_synthetique_dsu_seuil_bas = commune('rang_indice_synthetique_dsu_seuil_bas', period)
        rang_indice_synthetique_dsu_seuil_haut = commune('rang_indice_synthetique_dsu_seuil_haut', period)

        nombre_elig_seuil_bas = commune('dsu_nombre_communes_eligibles_seuil_bas', period)
        nombre_elig_seuil_haut = commune('dsu_nombre_communes_eligibles_seuil_haut', period)
        effort_fiscal = commune('effort_fiscal', period)
        population_insee = commune('population_insee', period)
        population_qpv = commune('population_qpv', period)
        # PLF population_zfu = commune('population_zfu', period)
        population_dgf = commune('population_dgf', period)
        indice_synthetique_dsu = commune('indice_synthetique_dsu', period)

        facteur_classement_max = parameters(period).dotation_solidarite_urbaine.attribution.facteur_classement_max
        facteur_classement_min = parameters(period).dotation_solidarite_urbaine.attribution.facteur_classement_min
        poids_quartiers_prioritaires_ville = parameters(period).dotation_solidarite_urbaine.attribution.poids_quartiers_prioritaires_ville
        # PLF : poids_zone_franche_urbaine = parameters(period).dotation_solidarite_urbaine.attribution.poids_zone_franche_urbaine
        plafond_effort_fiscal = parameters(period).dotation_solidarite_urbaine.attribution.plafond_effort_fiscal
        augmentation_max = parameters(period).dotation_solidarite_urbaine.attribution.augmentation_max
        seuil_bas = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_bas_nombre_habitants
        seuil_haut = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_haut_nombre_habitants

        pourcentage_augmentation_dsu = dsu_montant_total / dsu_an_precedent - 1

        eligible_groupe_haut = dsu_eligible * (seuil_haut <= population_dgf)
        eligible_groupe_bas = dsu_eligible * (seuil_bas <= population_dgf) * (seuil_haut > population_dgf)
        toujours_eligible_groupe_bas = eligible_groupe_bas * (montants_an_precedent > 0)
        toujours_eligible_groupe_haut = eligible_groupe_haut * (montants_an_precedent > 0)
        nouvellement_eligible_groupe_bas = eligible_groupe_bas * (montants_an_precedent == 0)
        nouvellement_eligible_groupe_haut = eligible_groupe_haut * (montants_an_precedent == 0)
        toujours_eligible = toujours_eligible_groupe_bas | toujours_eligible_groupe_haut
        # Détermination des scores
        facteur_classement_seuil_bas = where(rang_indice_synthetique_dsu_seuil_bas <= nombre_elig_seuil_bas, (facteur_classement_min - facteur_classement_max) * safe_divide((rang_indice_synthetique_dsu_seuil_bas - 1), (nombre_elig_seuil_bas - 1), 0) + facteur_classement_max, 0)
        facteur_classement_seuil_haut = where(rang_indice_synthetique_dsu_seuil_haut <= nombre_elig_seuil_haut, (facteur_classement_min - facteur_classement_max) * safe_divide((rang_indice_synthetique_dsu_seuil_haut - 1), (nombre_elig_seuil_haut - 1), 0) + facteur_classement_max, 0)
        facteur_classement = facteur_classement_seuil_bas + facteur_classement_seuil_haut
        facteur_effort_fiscal = min_(effort_fiscal, plafond_effort_fiscal)
        facteur_qpv = (1 + where(population_insee > 0, poids_quartiers_prioritaires_ville * population_qpv / population_insee, 0))
        # PLF : facteur_zfu = (1 + where(population_insee > 0, poids_zone_franche_urbaine * population_zfu / population_insee, 0))
        score_attribution = indice_synthetique_dsu * population_dgf * facteur_classement * facteur_effort_fiscal * facteur_qpv  # PLF : * facteur_zfu
        score_anciens_eligibles_groupe_haut = (score_attribution * toujours_eligible_groupe_haut)
        score_nouveaux_eligibles_groupe_haut = (score_attribution * nouvellement_eligible_groupe_haut)
        score_anciens_eligibles_groupe_bas = (score_attribution * toujours_eligible_groupe_bas)
        score_nouveaux_eligibles_groupe_bas = (score_attribution * nouvellement_eligible_groupe_bas)
        # clef de répartition groupe haut/groupe bas
        total_pop_eligible_augmentation_groupe_bas = (toujours_eligible_groupe_bas * population_dgf).sum()
        total_pop_eligible_augmentation_groupe_haut = (toujours_eligible_groupe_haut * population_dgf).sum()
        total_pop_eligible_augmentation = total_pop_eligible_augmentation_groupe_haut + total_pop_eligible_augmentation_groupe_bas
        # s'il n'y a pas de population, on répartit selon la population totale des groupes (non spécifié par la loi)
        if not total_pop_eligible_augmentation:
            total_pop_eligible_augmentation_groupe_bas = (eligible_groupe_bas * population_dgf).sum()
            total_pop_eligible_augmentation_groupe_haut = (eligible_groupe_haut * population_dgf).sum()
            total_pop_eligible_augmentation = total_pop_eligible_augmentation_groupe_haut + total_pop_eligible_augmentation_groupe_bas

        part_augmentation_groupe_bas = total_pop_eligible_augmentation_groupe_bas / total_pop_eligible_augmentation
        part_augmentation_groupe_haut = 1 - part_augmentation_groupe_bas
        # clef de répartition : on attribue une valeur des points d'augmentation égale au pourcentage
        # d'augmentation de la DSU
        rapport_valeur_point = pourcentage_augmentation_dsu  # Le rapport valeur point dépend
        # probablement du groupe, mais on ignore les détails de son calcul
        total_points_groupe_bas = (score_anciens_eligibles_groupe_bas * rapport_valeur_point + score_nouveaux_eligibles_groupe_bas).sum()
        total_points_groupe_haut = (score_anciens_eligibles_groupe_haut * rapport_valeur_point + score_nouveaux_eligibles_groupe_haut).sum()
        # Détermination de la valeur du point
        montant_garanti_eligible = (toujours_eligible * montants_an_precedent).sum()
        valeur_point_groupe_bas = (total_a_distribuer - montant_garanti_eligible) * part_augmentation_groupe_bas / total_points_groupe_bas if total_points_groupe_bas else 0
        valeur_point_groupe_haut = (total_a_distribuer - montant_garanti_eligible) * part_augmentation_groupe_haut / total_points_groupe_haut if total_points_groupe_haut else 0
        montant_toujours_eligible_groupe_bas = (min_(valeur_point_groupe_bas * rapport_valeur_point * score_attribution, augmentation_max) + montants_an_precedent) * toujours_eligible_groupe_bas
        montant_toujours_eligible_groupe_haut = (min_(valeur_point_groupe_haut * rapport_valeur_point * score_attribution, augmentation_max) + montants_an_precedent) * toujours_eligible_groupe_haut
        montant_nouvellement_eligible_groupe_bas = valeur_point_groupe_bas * score_attribution * nouvellement_eligible_groupe_bas
        montant_nouvellement_eligible_groupe_haut = valeur_point_groupe_haut * score_attribution * nouvellement_eligible_groupe_haut
        return montant_toujours_eligible_groupe_bas + montant_toujours_eligible_groupe_haut + montant_nouvellement_eligible_groupe_bas + montant_nouvellement_eligible_groupe_haut

    # La vraie clef de répartition n'est pas claire : les dotations sont distribuées
    # au prorata du score au sein des 4 sous catégories :
    # - groupe bas (entre 5000 et 9999 habitants DGF) nouvellement éligibles
    # - groupe bas (entre 5000 et 9999 habitants DGF) augmentation pour communes éligibles 2 ans de suite
    # - groupe haut (>= 10000 habitants DGF) nouvellement éligibles
    # - groupe haut (>= 10000 habitants DGF) augmentation pour communes éligibles 2 ans de suite
    # La répartition entre groupe haut et groupe bas se fait "au prorata de leur
    # population dans le total des communes bénéficiaires. "
    # En revanche, la répartition des dotations entre les nouvellement éligibles et toujours
    # éligibles n'est pas claire.
    # Ici, on :
    # Attribue au groupe haut et groupe bas en fonction des populations toujours éligibles
    # Pour la répartition au sein de chaque groupe, on veut que les rapports entre les valeurs de points pour la part spontanées
    # Et pour l'augmentation reflète la part entre la DSU de l'an dernier et l'augmentation totale (loi + CFL).
    # On veut donc :  VP(augmentation) / VP(dotation spontanée) = montant augmentation / montant an dernier
    # Ca correspond grosso modo (mais pas exactement) à la répartition de facto

    def formula_2019_01(commune, period, parameters):
        dsu_montant_total = commune('dsu_montant_total', period)
        dsu_an_precedent = commune('dsu_montant_total', period.last_year)
        montants_an_precedent = commune('dsu_montant_eligible', period.last_year)
        dsu_eligible = commune('dsu_eligible', period)
        total_a_distribuer = commune('dsu_montant_total_eligibles', period)
        rang_indice_synthetique_dsu_seuil_bas = commune('rang_indice_synthetique_dsu_seuil_bas', period)
        rang_indice_synthetique_dsu_seuil_haut = commune('rang_indice_synthetique_dsu_seuil_haut', period)

        nombre_elig_seuil_bas = commune('dsu_nombre_communes_eligibles_seuil_bas', period)
        nombre_elig_seuil_haut = commune('dsu_nombre_communes_eligibles_seuil_haut', period)
        effort_fiscal = commune('effort_fiscal', period)
        population_insee = commune('population_insee', period)
        population_qpv = commune('population_qpv', period)
        population_zfu = commune('population_zfu', period)
        population_dgf = commune('population_dgf', period)
        indice_synthetique_dsu = commune('indice_synthetique_dsu', period)

        facteur_classement_max = parameters(period).dotation_solidarite_urbaine.attribution.facteur_classement_max
        facteur_classement_min = parameters(period).dotation_solidarite_urbaine.attribution.facteur_classement_min
        poids_quartiers_prioritaires_ville = parameters(period).dotation_solidarite_urbaine.attribution.poids_quartiers_prioritaires_ville
        poids_zone_franche_urbaine = parameters(period).dotation_solidarite_urbaine.attribution.poids_zone_franche_urbaine
        plafond_effort_fiscal = parameters(period).dotation_solidarite_urbaine.attribution.plafond_effort_fiscal
        augmentation_max = parameters(period).dotation_solidarite_urbaine.attribution.augmentation_max
        seuil_bas = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_bas_nombre_habitants
        seuil_haut = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_haut_nombre_habitants

        pourcentage_augmentation_dsu = dsu_montant_total / dsu_an_precedent - 1

        eligible_groupe_haut = dsu_eligible * (seuil_haut <= population_dgf)
        eligible_groupe_bas = dsu_eligible * (seuil_bas <= population_dgf) * (seuil_haut > population_dgf)
        toujours_eligible_groupe_bas = eligible_groupe_bas * (montants_an_precedent > 0)
        toujours_eligible_groupe_haut = eligible_groupe_haut * (montants_an_precedent > 0)
        nouvellement_eligible_groupe_bas = eligible_groupe_bas * (montants_an_precedent == 0)
        nouvellement_eligible_groupe_haut = eligible_groupe_haut * (montants_an_precedent == 0)
        toujours_eligible = toujours_eligible_groupe_bas | toujours_eligible_groupe_haut
        # Détermination des scores
        facteur_classement_seuil_bas = where(rang_indice_synthetique_dsu_seuil_bas <= nombre_elig_seuil_bas, (facteur_classement_min - facteur_classement_max) * safe_divide((rang_indice_synthetique_dsu_seuil_bas - 1), (nombre_elig_seuil_bas - 1), 0) + facteur_classement_max, 0)
        facteur_classement_seuil_haut = where(rang_indice_synthetique_dsu_seuil_haut <= nombre_elig_seuil_haut, (facteur_classement_min - facteur_classement_max) * safe_divide((rang_indice_synthetique_dsu_seuil_haut - 1), (nombre_elig_seuil_haut - 1), 0) + facteur_classement_max, 0)
        facteur_classement = facteur_classement_seuil_bas + facteur_classement_seuil_haut
        facteur_effort_fiscal = min_(effort_fiscal, plafond_effort_fiscal)
        facteur_qpv = (1 + where(population_insee > 0, poids_quartiers_prioritaires_ville * population_qpv / population_insee, 0))
        facteur_zfu = (1 + where(population_insee > 0, poids_zone_franche_urbaine * population_zfu / population_insee, 0))
        score_attribution = indice_synthetique_dsu * population_dgf * facteur_classement * facteur_effort_fiscal * facteur_qpv * facteur_zfu
        score_anciens_eligibles_groupe_haut = (score_attribution * toujours_eligible_groupe_haut)
        score_nouveaux_eligibles_groupe_haut = (score_attribution * nouvellement_eligible_groupe_haut)
        score_anciens_eligibles_groupe_bas = (score_attribution * toujours_eligible_groupe_bas)
        score_nouveaux_eligibles_groupe_bas = (score_attribution * nouvellement_eligible_groupe_bas)
        # clef de répartition groupe haut/groupe bas
        total_pop_eligible_augmentation_groupe_bas = (toujours_eligible_groupe_bas * population_dgf).sum()
        total_pop_eligible_augmentation_groupe_haut = (toujours_eligible_groupe_haut * population_dgf).sum()
        total_pop_eligible_augmentation = total_pop_eligible_augmentation_groupe_haut + total_pop_eligible_augmentation_groupe_bas
        # s'il n'y a pas de population, on répartit selon la population totale des groupes (non spécifié par la loi)
        if not total_pop_eligible_augmentation:
            total_pop_eligible_augmentation_groupe_bas = (eligible_groupe_bas * population_dgf).sum()
            total_pop_eligible_augmentation_groupe_haut = (eligible_groupe_haut * population_dgf).sum()
            total_pop_eligible_augmentation = total_pop_eligible_augmentation_groupe_haut + total_pop_eligible_augmentation_groupe_bas

        part_augmentation_groupe_bas = total_pop_eligible_augmentation_groupe_bas / total_pop_eligible_augmentation
        part_augmentation_groupe_haut = 1 - part_augmentation_groupe_bas
        # clef de répartition : on attribue une valeur des points d'augmentation égale au pourcentage
        # d'augmentation de la DSU
        rapport_valeur_point = pourcentage_augmentation_dsu  # Le rapport valeur point dépend
        # probablement du groupe, mais on ignore les détails de son calcul
        total_points_groupe_bas = (score_anciens_eligibles_groupe_bas * rapport_valeur_point + score_nouveaux_eligibles_groupe_bas).sum()
        total_points_groupe_haut = (score_anciens_eligibles_groupe_haut * rapport_valeur_point + score_nouveaux_eligibles_groupe_haut).sum()
        # Détermination de la valeur du point
        montant_garanti_eligible = (toujours_eligible * montants_an_precedent).sum()
        valeur_point_groupe_bas = (total_a_distribuer - montant_garanti_eligible) * part_augmentation_groupe_bas / total_points_groupe_bas if total_points_groupe_bas else 0
        valeur_point_groupe_haut = (total_a_distribuer - montant_garanti_eligible) * part_augmentation_groupe_haut / total_points_groupe_haut if total_points_groupe_haut else 0
        montant_toujours_eligible_groupe_bas = (min_(valeur_point_groupe_bas * rapport_valeur_point * score_attribution, augmentation_max) + montants_an_precedent) * toujours_eligible_groupe_bas
        montant_toujours_eligible_groupe_haut = (min_(valeur_point_groupe_haut * rapport_valeur_point * score_attribution, augmentation_max) + montants_an_precedent) * toujours_eligible_groupe_haut
        montant_nouvellement_eligible_groupe_bas = valeur_point_groupe_bas * score_attribution * nouvellement_eligible_groupe_bas
        montant_nouvellement_eligible_groupe_haut = valeur_point_groupe_haut * score_attribution * nouvellement_eligible_groupe_haut
        return montant_toujours_eligible_groupe_bas + montant_toujours_eligible_groupe_haut + montant_nouvellement_eligible_groupe_bas + montant_nouvellement_eligible_groupe_haut


class indice_synthetique_dsu(Variable):
    value_type = float
    entity = Commune
    definition_period = YEAR
    label = "Indice synthétique DSU:\
        indice synthétique pour l'éligibilité à la DSU"
    reference = "https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000038834291&cidTexte=LEGITEXT000006070633"

    # dernier RFR connu (N-1) -> RFR antépénultième année (N-2)
    # la valeur en place est déjà celle à prendre pour 2026

    def formula_2025(commune, period, parameters):
        population_dgf = commune("population_dgf", period)
        outre_mer = commune('outre_mer', period)
        potentiel_financier = commune('potentiel_financier', period)
        potentiel_financier_par_habitant = commune('potentiel_financier_par_habitant', period)
        nombre_logements = commune('nombre_logements', period)
        nombre_logements_sociaux = commune('nombre_logements_sociaux', period)
        nombre_aides_au_logement = commune('nombre_beneficiaires_aides_au_logement', period)
        revenu = commune('revenu_total', period)
        population_insee = commune('population_insee', period)

        revenu_par_habitant = commune('revenu_par_habitant', period)
        # PLF : conserver la période pour la valeur
        # ou passer la période à N-1 (pour des données DGCL déjà en N-1) ?

        seuil_bas = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_bas_nombre_habitants
        seuil_haut = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_haut_nombre_habitants
        ratio_max_pot_fin = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_rapport_potentiel_financier
        poids_pot_fin = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_potentiel_financier
        poids_logements_sociaux = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_logements_sociaux
        poids_aides_au_logement = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_aides_au_logement
        poids_revenu = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_revenu

        groupe_bas = (~outre_mer) * (seuil_bas <= population_dgf) * (seuil_haut > population_dgf)
        groupe_haut = (~outre_mer) * (seuil_haut <= population_dgf)

        pot_fin_bas = (sum(groupe_bas * potentiel_financier)
                       / sum(groupe_bas * population_dgf)) if sum(groupe_bas * population_dgf) > 0 else 0
        pot_fin_haut = (sum(groupe_haut * potentiel_financier)
                        / sum(groupe_haut * population_dgf)) if sum(groupe_haut * population_dgf) > 0 else 0

        # Retrait des communes au potentiel financier trop élevé, les communes restantes ont droit à un indice synthétique
        # TODO extraire ces règles d'exclusion
        groupe_bas_score_positif = groupe_bas * (potentiel_financier_par_habitant < ratio_max_pot_fin * pot_fin_bas)
        groupe_haut_score_positif = groupe_haut * (potentiel_financier_par_habitant < ratio_max_pot_fin * pot_fin_haut)

        # Calcul des ratios moyens nécessaires au calcul de l'indice synthétique
        part_logements_sociaux_bas = (sum(groupe_bas * nombre_logements_sociaux)
                                      / sum(groupe_bas * nombre_logements)) if sum(groupe_bas * nombre_logements) > 0 else 0
        part_logements_sociaux_haut = (sum(groupe_haut * nombre_logements_sociaux)
                                       / sum(groupe_haut * nombre_logements)) if sum(groupe_haut * nombre_logements) > 0 else 0

        part_aides_logement_bas = (sum(groupe_bas * nombre_aides_au_logement)
                                   / sum(groupe_bas * nombre_logements)) if sum(groupe_bas * nombre_logements) > 0 else 0
        part_aides_logement_haut = (sum(groupe_haut * nombre_aides_au_logement)
                                    / sum(groupe_haut * nombre_logements)) if sum(groupe_haut * nombre_logements) > 0 else 0

        revenu_moyen_bas = (sum(groupe_bas * revenu)
                            / sum(groupe_bas * population_insee)) if sum(groupe_bas * population_insee) > 0 else 0
        revenu_moyen_haut = (sum(groupe_haut * revenu)
                             / sum(groupe_haut * population_insee)) if sum(groupe_haut * population_insee) > 0 else 0

        part_logements_sociaux_commune = safe_divide(nombre_logements_sociaux, nombre_logements)
        part_aides_logement_commune = safe_divide(nombre_aides_au_logement, nombre_logements)

        indice_synthetique_bas = groupe_bas_score_positif * (
            poids_pot_fin * safe_divide(pot_fin_bas, potentiel_financier_par_habitant)
            + poids_logements_sociaux * safe_divide(part_logements_sociaux_commune, part_logements_sociaux_bas)
            + poids_aides_au_logement * safe_divide(part_aides_logement_commune, part_aides_logement_bas)
            + poids_revenu * safe_divide(revenu_moyen_bas, revenu_par_habitant)
        )

        indice_synthetique_haut = groupe_haut_score_positif * (
            poids_pot_fin * safe_divide(pot_fin_haut, potentiel_financier_par_habitant)
            + poids_logements_sociaux * safe_divide(part_logements_sociaux_commune, part_logements_sociaux_haut)
            + poids_aides_au_logement * safe_divide(part_aides_logement_commune, part_aides_logement_haut)
            + poids_revenu * safe_divide(revenu_moyen_haut, revenu_par_habitant)
        )
        return indice_synthetique_bas + indice_synthetique_haut

    def formula(commune, period, parameters):
        population_dgf = commune("population_dgf", period)
        outre_mer = commune('outre_mer', period)
        potentiel_financier = commune('potentiel_financier', period)
        potentiel_financier_par_habitant = commune('potentiel_financier_par_habitant', period)
        nombre_logements = commune('nombre_logements', period)
        nombre_logements_sociaux = commune('nombre_logements_sociaux', period)
        nombre_aides_au_logement = commune('nombre_beneficiaires_aides_au_logement', period)
        revenu = commune('revenu_total', period)
        population_insee = commune('population_insee', period)
        revenu_par_habitant = commune('revenu_par_habitant', period)

        seuil_bas = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_bas_nombre_habitants
        seuil_haut = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_haut_nombre_habitants
        ratio_max_pot_fin = parameters(period).dotation_solidarite_urbaine.eligibilite.seuil_rapport_potentiel_financier
        poids_pot_fin = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_potentiel_financier
        poids_logements_sociaux = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_logements_sociaux
        poids_aides_au_logement = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_aides_au_logement
        poids_revenu = parameters(period).dotation_solidarite_urbaine.eligibilite.indice_synthetique.poids_revenu

        groupe_bas = (~outre_mer) * (seuil_bas <= population_dgf) * (seuil_haut > population_dgf)
        groupe_haut = (~outre_mer) * (seuil_haut <= population_dgf)

        pot_fin_bas = (sum(groupe_bas * potentiel_financier)
                       / sum(groupe_bas * population_dgf)) if sum(groupe_bas * population_dgf) > 0 else 0
        pot_fin_haut = (sum(groupe_haut * potentiel_financier)
                        / sum(groupe_haut * population_dgf)) if sum(groupe_haut * population_dgf) > 0 else 0

        # Retrait des communes au potentiel financier trop élevé, les communes restantes ont droit à un indice synthétique
        # TODO extraire ces règles d'exclusion
        groupe_bas_score_positif = groupe_bas * (potentiel_financier_par_habitant < ratio_max_pot_fin * pot_fin_bas)
        groupe_haut_score_positif = groupe_haut * (potentiel_financier_par_habitant < ratio_max_pot_fin * pot_fin_haut)

        # Calcul des ratios moyens nécessaires au calcul de l'indice synthétique
        part_logements_sociaux_bas = (sum(groupe_bas * nombre_logements_sociaux)
                                      / sum(groupe_bas * nombre_logements)) if sum(groupe_bas * nombre_logements) > 0 else 0
        part_logements_sociaux_haut = (sum(groupe_haut * nombre_logements_sociaux)
                                       / sum(groupe_haut * nombre_logements)) if sum(groupe_haut * nombre_logements) > 0 else 0

        part_aides_logement_bas = (sum(groupe_bas * nombre_aides_au_logement)
                                   / sum(groupe_bas * nombre_logements)) if sum(groupe_bas * nombre_logements) > 0 else 0
        part_aides_logement_haut = (sum(groupe_haut * nombre_aides_au_logement)
                                    / sum(groupe_haut * nombre_logements)) if sum(groupe_haut * nombre_logements) > 0 else 0

        revenu_moyen_bas = (sum(groupe_bas * revenu)
                            / sum(groupe_bas * population_insee)) if sum(groupe_bas * population_insee) > 0 else 0
        revenu_moyen_haut = (sum(groupe_haut * revenu)
                             / sum(groupe_haut * population_insee)) if sum(groupe_haut * population_insee) > 0 else 0

        part_logements_sociaux_commune = safe_divide(nombre_logements_sociaux, nombre_logements)
        part_aides_logement_commune = safe_divide(nombre_aides_au_logement, nombre_logements)

        indice_synthetique_bas = groupe_bas_score_positif * (
            poids_pot_fin * safe_divide(pot_fin_bas, potentiel_financier_par_habitant)
            + poids_logements_sociaux * safe_divide(part_logements_sociaux_commune, part_logements_sociaux_bas)
            + poids_aides_au_logement * safe_divide(part_aides_logement_commune, part_aides_logement_bas)
            + poids_revenu * safe_divide(revenu_moyen_bas, revenu_par_habitant)
        )

        indice_synthetique_haut = groupe_haut_score_positif * (
            poids_pot_fin * safe_divide(pot_fin_haut, potentiel_financier_par_habitant)
            + poids_logements_sociaux * safe_divide(part_logements_sociaux_commune, part_logements_sociaux_haut)
            + poids_aides_au_logement * safe_divide(part_aides_logement_commune, part_aides_logement_haut)
            + poids_revenu * safe_divide(revenu_moyen_haut, revenu_par_habitant)
        )
        return indice_synthetique_bas + indice_synthetique_haut


# pour une simulation du PLF 2026 sur la période 2025, si l'on ne modifiait pas dsu_montant_total
# le montant serait 2024 + augmentation au lieu de 2025 + augmentation au PLF
# on modifie donc dsu_montant_total, dsu_montant_outre_mer, dsu_montant_metropole
# et dsu_accroissement_metropole qu'elle appelle par cohérence.
class dsu_montant_total(Variable):
    value_type = float
    entity = Commune  # une valeur unique valable pour la métropole ; TODO passer à l'entité Etat ?
    definition_period = YEAR
    label = "DSU Montant hors garanties:\
        Valeur totale attribuée (hors garanties) aux communes éligibles à la DSU en métropole"
    reference = [
        "https://www.collectivites-locales.gouv.fr/sites/default/files/migration/note_dinformation_2019_dsu.pdf",
        "http://www.dotations-dgcl.interieur.gouv.fr/consultation/documentAffichage.php?id=120"
    ]
    documentation = '''
    En 2019 : La somme effectivement mise en répartition au profit
    des communes de métropole s'élève à 2 164 552 909 €
    (...)
    après prélèvement de la quote-part réservée aux communes des départements
    et collectivités d'outre-mer (126 185 741 €).

    En 2020 : La somme effectivement mise en répartition au profit
    des communes de métropole s'élève à 2 244 240 555 €
    (...)
    après prélèvement de la quote-part réservée aux communes des départements
    et collectivités d’outre-mer (136 498 095 €).
    '''

    def formula_2025(commune, period, parameters):
        # ERREUR de représentation de montant
        # si l'on return commune.etat('dsu_montant_metropole', period)
        # alors on obtient ce montant par commune -1406371382 alors que dsu_montant_metropole vaut 2_888_595_914
        # on utilise donc la formule de la variable dsu_montant_metropole à la place de la formule la variable historique dsu_montant_total
        # à terme, le nom de la variable dsu_montant_total devrait être remplacée par dsu_montant_metropole et son unité passer de Commune à Etat
        dsu_montant_national = parameters(period).dotation_solidarite_urbaine.montant.total + parameters(period).dotation_solidarite_urbaine.augmentation_montant
        dsu_montant_outre_mer = commune.etat('dsu_montant_outre_mer', period)

        dsu_montant_metropole = dsu_montant_national - dsu_montant_outre_mer

        # TODO passer à l'entité Etat ; en attendant, même valeur attribuée à toutes y compris outre-mer alors que la variable est dédiée à la métropole
        nombre_national_communes = len(commune('nom', period.first_month))
        return full(nombre_national_communes, dsu_montant_metropole)

    # A partir de 2020, formule récursive qui bouge en
    # fonction des pourcentages
    # d'augmentation constatés (en vrai il faudrait défalquer
    # des pourcentages de population d'outre-mer)
    # mais c'est une autre histoire
    # La variation sera égale à pourcentage_accroissement *
    # valeur du paramètre "accroissement" pour cette année là.

    def formula_2020_01(commune, period, parameters):
        # Historique : esprit de la formule utilisée en 2020/2021
        # lié à dsu_accroissement_metropole + montant d'augmentation d'enveloppe fixe
        # accroissement = parameters(period).dotation_solidarite_urbaine.augmentation_montant
        # return montants_an_precedent + accroissement * pourcentage_accroissement_dsu_annee_courante
        # Sachant également qu'à partir de 2024, on distingue la majoration CFL dans majoration_montant.
        # Cette majoration était précédemment incluse dans augmentation_montant.

        montants_an_precedent = commune('dsu_montant_total', period.last_year)
        dsu_accroissement_metropole = commune.etat('dsu_accroissement_metropole', period)
        return montants_an_precedent + (montants_an_precedent * dsu_accroissement_metropole)

    # Est un montant fixe pour 2019

    def formula_2019_01(commune, period, parameters):
        dsu_effective_2019 = parameters(period).dotation_solidarite_urbaine.montant.metropole
        montant_total_a_attribuer = dsu_effective_2019
        return montant_total_a_attribuer

    # formule 2013 pour les tests seulement ?

    def formula_2013_01(commune, period, parameters):
        # TODO prendre en compte dotation_solidarite_urbaine.majoration_montant après ajout de ses valeurs 2013>2018
        # d'ici-là, la majoration est incluse dans augmentation_montant
        montants_an_prochain = commune('dsu_montant_total', period.offset(1, 'year'))
        accroissement = parameters(period.offset(1, 'year')).dotation_solidarite_urbaine.augmentation_montant
        pourcentage_accroissement_dsu_2020 = commune.etat('dsu_accroissement_metropole', '2020')
        return montants_an_prochain - accroissement * pourcentage_accroissement_dsu_2020  # TODO % à adapter à 2013


# WARNING : variable dsu_montant_metropole mise à jour mais favoriser l'emploi de dsu_montant_total
# parce que le test_enveloppes_budgétaires détecte une erreur de calcul probablement liée
# aux float32 et projections Etat/Communes
class dsu_montant_metropole(Variable):
    value_type = int
    entity = Etat
    definition_period = YEAR
    label = "Montant de l'enveloppe métropole de la DSU"

    # attention : formule copiée dans dsu_montant_total
    def formula(etat, period, parameters):
        '''
        Déduit le montant d'enveloppe DSU des communes de métropole suite
        au calcul de sa quote-part outre-mer.
        Equivaut au calcul du paramètre dotation_solidarite_urbaine.montant.metropole
        en cas d'évolution de l'enveloppe totale DSU.
        '''
        # PLF 2026 simulé en 2025 : l'enveloppe totale 2025 = montant total 2025 effectif + augmentation PLF 2026
        dsu_montant_national = parameters(period).dotation_solidarite_urbaine.montant.total + parameters(period).dotation_solidarite_urbaine.augmentation_montant
        dsu_montant_outre_mer = etat('dsu_montant_outre_mer', period)

        dsu_montant_metropole = dsu_montant_national - dsu_montant_outre_mer
        return dsu_montant_metropole


class dsu_montant_outre_mer(Variable):
    value_type = int
    entity = Etat
    definition_period = YEAR
    label = "Montant de la quote-part de DSU allouée aux communes ultra-marines"

    def formula_2025(etat, period, parameters):
        enveloppe_dnp_plf = parameters(period).dotation_nationale_perequation.montant.total
        # DNP : l'article 2334-13 modifié par l'article 72 du PLF 2026 conserve cette phrase (3ème alinéa) :
        # "Le montant mis en répartition au titre de la dotation nationale de péréquation
        # est au moins égal à celui mis en répartition l'année précédente."
        # + ⚠️ hypothèse : le CFL qui n'a pas majoré ce montant depuis 2015
        # (cf. note DGCL DNP 2025, page 2) ne le changerait pas suite à ce PLF.
        enveloppe_dsr_plf = parameters(period).dotation_solidarite_rurale.montant.total + parameters(period).dotation_solidarite_rurale.augmentation_montant
        enveloppe_dsu_plf = parameters(period).dotation_solidarite_urbaine.montant.total + parameters(period).dotation_solidarite_urbaine.augmentation_montant

        dgf_montant_perequation_verticale_communale = enveloppe_dnp_plf + enveloppe_dsr_plf + enveloppe_dsu_plf

        portion_dsu_enveloppe_perequation = enveloppe_dsu_plf / dgf_montant_perequation_verticale_communale
        dacom_montant_total = etat('dacom_montant_total', period)
        dsu_montant_outre_mer = round(portion_dsu_enveloppe_perequation * dacom_montant_total)
        return dsu_montant_outre_mer

    def formula(etat, period, parameters):
        # info : Tant que les calculs sont réalisés en float32, dgf_montant_perequation_verticale_communale
        # doit être calculé dans cette formule pour éviter des erreurs de précisions
        # à l'association de ce nombre en Md€ à des nombres à décimales.
        enveloppe_dnp = parameters(period).dotation_nationale_perequation.montant.total + 0
        enveloppe_dsr = parameters(period).dotation_solidarite_rurale.montant.total + parameters(period).dotation_solidarite_rurale.augmentation_montant
        enveloppe_dsu = parameters(period).dotation_solidarite_urbaine.montant.total + parameters(period).dotation_solidarite_urbaine.augmentation_montant
        dgf_montant_perequation_verticale_communale = enveloppe_dnp + enveloppe_dsr + enveloppe_dsu

        # info : calcul dsu_montant_outre_mer déduit des montants effectifs 2024 et 2025
        # logique = la DSU outre-mer est à l'échelle de la part de contribution
        # de la DSU nationale à l'assiette de la DACOM (enveloppe de péréquation verticale)
        portion_dsu_enveloppe_perequation = enveloppe_dsu / dgf_montant_perequation_verticale_communale
        dacom_montant_total = etat('dacom_montant_total', period)
        dsu_montant_outre_mer = round(portion_dsu_enveloppe_perequation * dacom_montant_total)
        return dsu_montant_outre_mer


class dsu_accroissement_metropole(Variable):
    value_type = float
    entity = Etat
    definition_period = YEAR
    label = "En métropole, pourcentage d'accroissement de la dotation de solidarité urbaine et de cohésion sociale (DSU) \
        par rapport à l'année passée"
    # reference
    documentation = '''
    2019) "La somme effectivement mise en répartition au profit des communes de métropole
    s'élève à 2 164 552 909 €"

    2020) La somme effectivement mise en répartition au profit des communes de métropole
    s'élève à 2 244 240 555 €"

    2021) "La somme effectivement mise en répartition au profit des communes de métropole
    s'élève à 2 320 959 120 €"
    '''

    def formula_2025(etat, period, parameters):
        # pour le PLF 2026
        dsu_effective_annee_precedente = parameters(period).dotation_solidarite_urbaine.montant.metropole  # 2025 effectif
        dsu_annee_courante = etat.members('dsu_montant_total', period)[0]  # montant 2026 enregistré ici sous la période 2025 et calculé sur enveloppe effective 2025 + augmentation PLF 2026

        pourcentage_accroissement_dsu_annee_courante = (dsu_annee_courante - dsu_effective_annee_precedente) / dsu_effective_annee_precedente
        return pourcentage_accroissement_dsu_annee_courante

    def formula_2020_01(etat, period, parameters):
        # Historique : esprit de la formule utilisée en 2020/2021
        # = accroissement = delta d'enveloppe de fraction entre deux années successives relativement à l'augmentation d'enveloppe générale, ici, de l'année la plus ancienne
        # (enveloppe d'augmentation par L.2334-13 du CGCT + majoration décidée par le Comité des finances locales)
        # ! attention : ordre inversé par rapport aux accroissements des trois fractions de DSR (raison non identifiée)
        # dsu_effective_annee_passee = parameters(period.last_year).dotation_solidarite_urbaine.montant.metropole
        # dsu_effective_annee_courante = parameters(period).dotation_solidarite_urbaine.montant.metropole
        # dsu_accroissement_annee_courante = parameters(period).dotation_solidarite_urbaine.augmentation_montant
        # pourcentage_accroissement_dsu_annee_courante = (dsu_effective_annee_passee - dsu_effective_annee_courante) / dsu_accroissement_annee_courante

        # formule corrigée en 2024 (openfisca-france-dotations-locales > v.3.0.2)
        # afin de reproduire les % indiqués dans la note DGCL
        # = delta d'enveloppe de fraction entre deux années successives relativement à l'enveloppe de la fraction en début de période
        dsu_effective_annee_precedente = parameters(period.last_year).dotation_solidarite_urbaine.montant.metropole
        dsu_annee_courante = parameters(period).dotation_solidarite_urbaine.montant.metropole

        pourcentage_accroissement_dsu_annee_courante = (dsu_annee_courante - dsu_effective_annee_precedente) / dsu_effective_annee_precedente
        return pourcentage_accroissement_dsu_annee_courante


# dacom_montant_total ajoutée pour compléter dsu_montant_outre_mer
class dacom_montant_total(Variable):
    value_type = float
    entity = Etat
    definition_period = YEAR
    label = "Montant total de la quote-part de la dotation d'aménagement des communes d'outre-mer (DACOM)"
    reference = [
        "I de l'article L. 2334-23-1 du Code général des collectivités territoriales (CGCT)",
        "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000046873826/2023-01-01"
    ]
    documentation = '''
    [objet] Extrait de la note DGCL DACOM 2025, page 2 :
    Le mode de calcul de la dotation d'aménagement ultramarine traduit la solidarité nationale
    en faveur des communes d'outre-mer en leur affectant une quote-part plus favorable
    que celle résultant de leur strict poids démographique.

    [calcul] Extrait de l'article L. 2334-23-1 :
    I. - A compter de 2020, la quote-part de la dotation d'aménagement (...)
    destinée aux communes des départements d'outre-mer, de la Nouvelle-Calédonie,
    de la Polynésie française, de la collectivité territoriale de Saint-Pierre-et-Miquelon
    et aux circonscriptions territoriales de Wallis-et-Futuna comprend
    une dotation d'aménagement des communes d'outre-mer
    [et, s'agissant des communes des départements d'outre-mer, une dotation de péréquation].

    Cette quote-part est calculée en appliquant à la somme des montants
    de la dotation nationale de péréquation, de la dotation de solidarité rurale
    et de la dotation de solidarité urbaine et de cohésion sociale le rapport existant,
    d'après le dernier recensement de population, entre la population des communes d'outre-mer
    et la population de l'ensemble des communes. Ce rapport est majoré de 63 % en 2023.
    '''

    def formula(etat, period, parameters):
        # info : On choisit d'employer les paramètres d'enveloppe déductibles de la loi
        # et non les variables simulées plus sensibles aux marges d'erreur.
        # PLF 2026 simulé en 2025 : les enveloppes totales 2025 = montant total 2025 effectif + augmentation PLF 2026
        # pas de majoration du CFL
        enveloppe_dnp = parameters(period).dotation_nationale_perequation.montant.total + 0
        enveloppe_dsr = parameters(period).dotation_solidarite_rurale.montant.total + parameters(period).dotation_solidarite_rurale.augmentation_montant
        enveloppe_dsu = parameters(period).dotation_solidarite_urbaine.montant.total + parameters(period).dotation_solidarite_urbaine.augmentation_montant

        # info : Tant que les calculs sont réalisés en float32, dgf_montant_perequation_verticale_communale
        # doit être calculé dans cette formule pour éviter des erreurs de précisions
        # à l'association de ce nombre en Md€ au ratio_demographique_outre_mer à parfois 11 décimales.
        dgf_montant_perequation_verticale_communale = enveloppe_dnp + enveloppe_dsr + enveloppe_dsu

        ratio_demographique_outre_mer = etat('ratio_demographique_outre_mer', period)
        dacom_montant_total = ceil(ratio_demographique_outre_mer * dgf_montant_perequation_verticale_communale)
        # info : 'ceil' employé pour arrondir à l'entier surpérieur dès le premier cent
        # calcul déduit de la note DGCL DACOM 2024 (en 2024 : 388_891_981.12238264 arrondi à 388_891_982)
        return dacom_montant_total
