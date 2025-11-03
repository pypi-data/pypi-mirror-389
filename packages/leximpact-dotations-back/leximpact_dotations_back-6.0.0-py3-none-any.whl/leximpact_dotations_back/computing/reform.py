import logging
from typing import Dict

from openfisca_core import periods
from openfisca_core.parameters import Parameter
from openfisca_core.reforms import Reform

from leximpact_dotations_back.mapping.reform_parameters import get_openfisca_parameter
from leximpact_dotations_back.computing.dotations_simulation import DotationsSimulation
from leximpact_dotations_back.computing.reform_plf_2026_variables import (
    dsr_montant_garantie_non_eligible_fraction_bourg_centre,
    indice_synthetique_dsr_cible,
    dsr_montant_garantie_non_eligible_fraction_cible,
    dsu_montant_total,
    dsu_montant_metropole,
    dsu_montant_outre_mer,
    dacom_montant_total,
    dsu_accroissement_metropole,
    dsu_montant_eligible,
    indice_synthetique_dsu
)

# configure _root_ logger
logger = logging.getLogger()


class reform_from_amendement(Reform):
    name = 'Amendement'

    # Exemple d'amendement_parameters = {
    #     "dotation_solidarite_rurale.seuil_nombre_habitants": 5000,
    #     "dotation_solidarite_rurale.augmentation_montant": 100_000_000
    # }

    def __init__(self, baseline, amendement_parameters, reform_year):
        # on définit amendement_parameters avant l'appel à super
        # à défaut on obtient cette erreur à l'exécution (du apply)
        # AttributeError: 'CountryTaxBenefitSystem' object has no attribute 'amendement_parameters'
        self.amendement_parameters: Dict[str, float] = amendement_parameters
        self.reform_year = reform_year
        super().__init__(baseline)

    def reform_parameters_from_amendement(self, parameters, amendement_parameters):
        reform_period = periods.period(self.reform_year)

        for parameter_name, value in amendement_parameters.items():
            try:
                one_parameter: Parameter = get_openfisca_parameter(parameters, parameter_name)
                if one_parameter is not None:
                    one_parameter.update(period=reform_period, value=value)
            except ValueError as e:
                # TODO ajouter l'information à la réponse d'API web ?
                logger.warning(f"[Amendement] Échec de la réforme du paramètre '{parameter_name}': {e}")

        return parameters

    def apply(self):
        self.modify_parameters(
            modifier_function=lambda parameters: self.reform_parameters_from_amendement(parameters, self.amendement_parameters)
        )


# DOCUMENTATION : liste des paramètres modifiés par le PLF 2026
# n'est pas employée par le calcul qui utilisera l'attribut 'parameters'
# dont la valeur sera issue de la requête à l'API ('request.plf.dotations')
PLF_2026_PARAMETERS = {
    # Enveloppe DGF (invisible sur l'interface du simulateur)
    # article L. 1613-1 + article 31 du PLF 2026
    # Extrait de l'exposé des motifs :
    # "A périmètre courant, le montant nominal de la DGF augmente
    # donc de 5 183 681 189 € par rapport à 2025."
    # et cela "résulte simplement de mesures de périmètre".
    # rappel, montant effectif 2025 : 27_394_686_833 €
    "montant_dotation_globale_fonctionnement": 32_578_368_022,

    # Abondement de l'Etat à la DGF
    # article 72 du PLF, exposé des motifs, 1.
    "dotation_globale_fonctionnement.montant_abondement_etat": 290_000_000,
    "dotation_globale_fonctionnement.communes.montant_abondement_etat": 290_000_000,

    # DF / DI : Enveloppe de la dotation d'intercommunalité utilisée
    # pour le calcul d'écrêtement de DF
    # article 72 du PLF, exposé des motifs, 2.
    # d'ordinaire référencée par le II de l'Article L5211-28 du CGCT
    # pas de modification affectant cette partie dans le PLF mais texte permettant
    # déjà le renouvellement de cette augmentation à partir de 2024.
    # confirmé par l'annexe RCT (Relations avec les collectivités territoriales) au PLF 2026, page 8, 1.
    # https://www.budget.gouv.fr/documentation/documents-budgetaires-lois/exercice-2026/plf-2026?docuement_dossier%5B0%5D=mission_nomenclature%3A92743
    "dotation_intercommunalite.augmentation_montant": 90_000_000,

    # Enveloppes DSR et DSU
    # article L. 2334-13 - LEGIARTI000048849554
    "dotation_solidarite_urbaine.augmentation_montant": 140_000_000,
    "dotation_solidarite_rurale.augmentation_montant": 150_000_000,

    # Majorations du CFL inconnues ; décision à venir début 2026
    "dotation_solidarite_urbaine.majoration_montant": 0,
    "dotation_solidarite_rurale.majoration_montant": 0,

    # par cohérence, on souhaiterait propagee l'augmentation aux autres paramètres liés total et métropole
    # mais cela ne peut pas être fait tant que la simulation du PLF 2026 se fait en année de simulation 2025
    # parce que des formules telles que dsu_montant_metropole et dsu_montant_outre_mer
    # emploient ces montants totaux 2025 comme étant les montants effectivement attribués en 2025
    # "dotation_solidarite_urbaine.montant.total": 2_955_738_650 + 140_000_000,
    # "dotation_solidarite_rurale.montant.total": 2_377_344_903 + 150_000_000,

    # DNP : dotation_nationale_perequation.montant reste inchangé
    # d'après l'exposé des motifs de l'article 72 du PLF 2026
}


class reform_from_plf(Reform):
    name = 'PLF 2026'

    # Enveloppe totale DGF
    # article L. 1613-1 - (invisible sur l'interface du simulateur) - article 31 du PLF 2026
    # + 5_183_681_189 € par rapport à l'année précédente (cité dans l'exposé des motifs)
    # = 32_578_368_022 - 27_394_686_833

    # Enveloppes DSR et DSU
    # article L. 2334-13 - LEGIARTI000048849554

    # DSR
    # éligibilité - article L.2334-20 - LEGIARTI000048849509
    # 60% borne minimale péréquation avant décision CFL
    # TODO ajouter sur l'UI une carte CFL et au back un paramètre

    # DSR bourg-centre - article L.2334-21 - LEGIARTI000036433099
    # voir leximpact_dotations_back.computing.reform_plf_2026_variables.dsr_montant_garantie_non_eligible_fraction_bourg_centre

    # DSR cible - article 2334-22-1 - LEGIARTI000037994647 - indice synthétique
    # voir leximpact_dotations_back.computing.reform_plf_2026_variables.indice_synthetique_dsr_cible

    # DSU
    # article L.2334-16 - LEGIARTI000044980780 - éligibilité
    # précédemment, les communes suivantes [étaient exclues de la DSU
    # parce que] n'étaient pas considérées comme des communes de 10 000 habitants et plus :
    # I de l'article L2334-22-2 :
    # "Par dérogation, peuvent être éligibles aux trois fractions de la dotation de solidarité rurale
    # les communes nouvelles mentionnées à l'article L. 2113-1 créées après la promulgation
    # de la loi n° 2010-1563 du 16 décembre 2010 de réforme des collectivités territoriales
    # qui comptent 10 000 habitants ou plus et qui remplissent les conditions cumulatives suivantes :
    # 1° Aucune des communes anciennes ne comptait, l'année précédant la fusion, 10 000 habitants ou plus ;
    # 2° Elles sont caractérisées comme peu denses ou très peu denses, au sens
    # de l'Institut national de la statistique et des études économiques
    # et selon les données disponibles sur le site internet de cet institut
    # au 1er janvier de l'année de répartition. Dans le cas où cette donnée
    # n'est pas disponible à l'échelle d'une commune nouvelle, cette dernière
    # est considérée comme peu dense ou très peu dense si l'ensemble des anciennes
    # communes sont, dans les mêmes conditions, considérées comme peu denses ou très peu denses."
    #
    # => certaines communes nouvelles de 10 000 habitants ou plus pouvaient
    # avoir la DSR par dérogation mais étaient exclues de la DSU.
    # TODO non modélisé donc suppression non modélisable

    # article L. 2334-18-2 - LEGIARTI000048849512 - répartition > attribution
    # suppression du facteur QPV
    # voir leximpact_dotations_back.computing.reform_plf_2026_variables.dsu_montant_eligible

    # article L. 2334-17 - LEGIARTI000038834291 - répartition > indice synthétique
    # dernier RFR connu (N-1) -> RFR antépénultième année (N-2)

    # DF - article L. 2334-7 - LEGIARTI000048849596
    # TODO dans 'dotation_forfaitaire', retraitement de la DF
    # des part CPS et TASCOM non modélisé
    # donc suprression non modélisable

    # DCN
    # pas de modification par le PLF

    def __init__(self, baseline, plf_parameters: Dict[str, int | float], reform_year):
        # on définit plf_parameters avant l'appel à super
        # à défaut on obtient cette erreur à l'exécution (du apply)
        # AttributeError: 'CountryTaxBenefitSystem' object has no attribute 'plf_parameters'
        self.plf_parameters: Dict[str, float] = plf_parameters  # exemple de valeur : voir PLF_2026_PARAMETERS
        self.reform_year = reform_year
        super().__init__(baseline)

    def reform_parameters_from_plf(self, parameters, plf_parameters):
        reform_period = periods.period(self.reform_year)

        for parameter_name, value in plf_parameters.items():

            try:
                one_parameter: Parameter = get_openfisca_parameter(parameters, parameter_name)
                if one_parameter is not None:
                    one_parameter.update(period=reform_period, value=value)
            except ValueError as e:
                # TODO ajouter l'information à la réponse d'API web ?
                logger.warning(f"[PLF] Échec de la réforme du paramètre '{parameter_name}': {e}")

        return parameters

    def apply(self):
        # WARNING : montants d'enveloppes budgétaires aussi définis à la création de la simulation
        # par set_dotations_enveloppes_previous_year et set_dotations_enveloppes_current_year

        self.modify_parameters(
            modifier_function=lambda parameters: self.reform_parameters_from_plf(parameters, self.plf_parameters)
        )

        # réformes structurelles PLF 2026
        self.update_variable(dsr_montant_garantie_non_eligible_fraction_bourg_centre)
        self.update_variable(indice_synthetique_dsr_cible)
        self.update_variable(dsr_montant_garantie_non_eligible_fraction_cible)
        self.update_variable(dsu_montant_total)
        self.update_variable(dsu_montant_metropole)
        self.update_variable(dsu_montant_outre_mer)
        self.update_variable(dacom_montant_total)
        self.update_variable(dsu_accroissement_metropole)
        self.update_variable(dsu_montant_eligible)
        self.update_variable(indice_synthetique_dsu)


def get_reformed_dotations_simulation(
        reform_model,
        data_directory,
        year_period,
        futureReform=False
) -> DotationsSimulation:
    dotations_simulation = DotationsSimulation(
        data_directory=data_directory,  # TODO optimiser en évitant le retraitement de criteres et adapted_criteres
        model=reform_model,
        futureModel=futureReform,
        annee=year_period
    )

    return dotations_simulation
