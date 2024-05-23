import re
import base64
import chardet
import pandas as pd
import os
import csv
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

# from .rdp_1 import Parser

class FileSerializer(serializers.Serializer):
    file_base64 = serializers.CharField(write_only=True)
    file_name = serializers.CharField(write_only=True)

class FileUploadView(APIView):

    def getTypeContact(self, nom):
        # Mots-clés pour identifier les personnes morales publiques
        contact_moral_public = ["COMMUNE", "DEPARTEMENT", "REGION", "ETAT", "COM", "DEP"]

        # Mots-clés pour identifier les personnes morales privées
        contact_moral_prive = ["SA", "SOCIETE ANONYME", "SARL", "SOCIETE A RESPONSABILITE LIMITEE", "SAS", "SCI"]

        # Convertir le nom en majuscules pour la recherche insensible à la casse
        nom_upper = nom.upper()

        # Vérification si le nom contient des mots-clés de personne morale publique
        for mot in contact_moral_public:
            if mot in nom_upper:
                print("Personne morale publique")
                return 4

        # Vérification si le nom contient des mots-clés de personne morale privée
        for mot in contact_moral_prive:
            if mot in nom_upper:
                print("Personne morale privée")
                return 3

        return 1


    # # Fonction pour extraire la 6ème donnée du tableau
    # def extract_data(table):
    #     data = table.find_all('td')
    #     if len(data) >= 6:
    #         sixth_data = data[5].text.strip()
    #         # Nettoyer le texte en ne gardant que les caractères alphabétiques
    #         cleaned_data = re.sub(r'[^a-zA-Z\s]', '', sixth_data)
    #         print(sixth_data)
    #         return cleaned_data.strip()
    #     else:
    #         return None


    # def extract_data(self, table):
    #     print("je suis dans la méthode statique")
    #     data = table.find_all('td')
    #     if len(data) >= 6:
    #         sixth_data = data[5].text.strip()
    #         # Nettoyer le texte en ne gardant que les caractères alphabétiques
    #         cleaned_data = re.sub(r'[^a-zA-Z\s]', '', sixth_data)
    #         return cleaned_data.strip()
    #     else:
    #         return None

    def parse_html_type1(self, file_content, html_file_path):
        # Initialiser BeautifulSoup avec le contenu HTML
        soup = BeautifulSoup(file_content, 'html.parser')

        file_name = "myFile"

        excel_file_path = os.path.join(os.path.dirname(html_file_path), file_name + ".xlsx")

        tables = soup.find_all('table')

        tables_with_pandas = [pd.read_html(str(table), flavor='bs4')[0] for table in tables]

        rows_data = []  # Pour stocker les données des lignes correspondantes

        for idx, table_df in enumerate(tables_with_pandas):
            # Parcourir chaque ligne du DataFrame
            for index, row in table_df.iterrows():
                # Vérifier si le premier élément de la ligne contient "ANNEE DE MAJ"
                if row[0] == "ANNEE DE MAJ":
                    # Ajouter uniquement les données de l'élément à la position 5
                    rows_data.append(row[5])

        print("Commune :")
        for data in rows_data:
            commune = re.sub(r'\b\d+\b\s+', '', data)
            print(commune)

        # Lecture du fichier CSV pour obtenir les codes postaux des communes
        # csv_file = '/home/yabdelmalek/qef_api/excelparser/BddCommunes.csv'
        # postal_codes = {}
        # try:
        #     with open(csv_file, mode='r', encoding='iso-8859-1') as file:
        #         print("Fichier CSV ouvert avec succès.")

        #         reader = csv.DictReader(file, delimiter=';')
        #         for row in reader:
        #             postal_codes[row['Nom']] = {'Code postal': row['Code postal'], 'Département': row['Département']}
        #         print("Postal codes:")
        #         print(postal_codes)

        # except Exception as e:
        #     print("Une erreur s'est produite lors de la lecture du fichier CSV :", str(e))

        #======================================================================================================================

        # Supprimer toutes les balises ayant la classe "TitreCR"
        for balise in soup.find_all(class_="TitreCR"):
            balise.extract()

        # Trouver toutes les lignes du tableau représentées par des balises <tr>
        lignes_tableau = soup.find_all('tr')

        # Initialiser un dictionnaire pour stocker les données extraites
        donnees_parcelles = {"Parcelles": []}

        # Parcourir toutes les lignes du tableau
        for ligne in lignes_tableau:
            # Vérifier si la ligne contient une seule cellule avec colspan="2"
            cellule_colspan_2 = ligne.find("td", {"colspan": "2"})
            if cellule_colspan_2:
                # Extraire le texte de cette cellule comme le nom
                nom = cellule_colspan_2.text.strip()
                # Obtenir le nom de la commune à partir de la variable commune
                commune = re.sub(r'\b\d+\b\s+', '', commune)
                continue  # Passer à la prochaine itération, car cette ligne ne contient pas les autres données

            # Extraire les cellules de chaque ligne représentées par des balises <td>
            cellules = ligne.find_all('td')

            # Vérifier s'il y a suffisamment de cellules dans la ligne
            if len(cellules) >= 6:
                # Extraire les données pertinentes des cellules
                an = cellules[0].text.strip()
                section = cellules[1].text.strip()
                numero_plan = cellules[2].text.strip()
                adresse = cellules[5].text.strip()
                code_rivioli = cellules[6].text.strip()

                # Vérifier si toutes les valeurs extraites ne sont pas des valeurs d'en-tête
                if an and section and numero_plan and adresse and code_rivioli and \
                        an != "AN" and section != "SECTION" and numero_plan != "N°PLAN" and adresse != "ADRESSE" and code_rivioli != "CODE RIVIOLI":
                    # Obtenir le code postal et le département de la commune actuelle à partir du dictionnaire postal_codes
                    # commune_info = postal_codes.get(commune, {"Code postal": "Code postal non trouvé", "Département": "Département non trouvé"})
                    # postal_code = commune_info["Code postal"]
                    # departement = commune_info["Département"]
                    type_contact = self.getTypeContact(nom)
                    parcelle = {
                        "NOM": nom,
                        "AN": an,
                        "SECTION": section,
                        "N PLAN": numero_plan,
                        "COMMUNE": commune,
                        "ADRESSE": adresse,
                        # "CODE": postal_code,
                        # "DEPARTEMENT": departement,
                        "TYPEID": type_contact
                    }

                    # Ajouter les données de la parcelle au dictionnaire de toutes les parcelles
                    donnees_parcelles["Parcelles"].append(parcelle)

        return donnees_parcelles





    def post(self, request, *args, **kwargs):

        print("-----------------------")
        # Récupérer la chaîne base64 du corps de la requête
        file_content_base64 = request.body.decode('utf-8')
        # Décoder la chaîne base64 pour obtenir le contenu du fichier
        file_content = base64.b64decode(file_content_base64)

        print("-----------------------")

        html_file_path = "votre_nom_de_fichier_ici.html"
        with open(html_file_path, 'wb') as file:
            file.write(file_content)
        print("-----------------------")

        with open(html_file_path, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding']
        with open(html_file_path, 'r', encoding=encoding) as file:
            file_content = file.read()

        parser = Parser(html_file_path)

        if "<title>Document</title>" in file_content:
            parsed_data = parser.run()
            print("################################")

            print("Parsed data :")

            print(parsed_data)

            return Response(parsed_data, status=status.HTTP_201_CREATED)

        elif "RELEVE DE PROPRIETE" in file_content:
            parsed_data = self.parse_html_type1(file_content, html_file_path)
            print("Releve de propriete")
            print(parsed_data)
            return Response(parsed_data, status=status.HTTP_201_CREATED)



        # parsed_data = self.parse_html_type1(file_content)



        # Retourner les données analysées
        # return Response(parsed_data, status=status.HTTP_201_CREATED)



        # =========================================================================================================

KEYWORDSDESIGNATION = ["propriétaire", "usufruitier", 'Usufruitière']


def makeHTMLreadable(html):
    clean_text = re.sub(r'<[^>]*>', '|', html)
    while "&nbsp;" in clean_text:
        clean_text = clean_text.replace('&nbsp;', " ")
    return clean_text


def extractDateOfBirth(text):
    text = text.replace("née", "né")
    pattern = r'né\s+le\s+(\d{2}/\d{2}/\d{4})'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return "empty"


def extractPropriete(text):
    print("Extract Propriete ##############################")

    proprieteDataDict = dict()
    proprieteDataDict['commune'] = ""
    proprieteDataDict['departement'] = ""
    proprieteDataDict['propriete'] = ""


    pattern = r"PROPRIETE\s(\d{3,10})"
    patternCommune = r"Commune : (\w+)"
    patternDepartement = r"Département : (\w+)\s*\((\d+)\)"
    # match = re.search(pattern, patternCommune, patternDepartement, text)
    match = re.search(patternCommune, text)
    match2 = re.search(patternDepartement, text)
    match3 = re.search(pattern, text)
    print(match)
    print(match2)
    print(match3)


    if match:
        proprieteDataDict['commune'] = match.group(1)

    if match2:
        proprieteDataDict['departement'] = match2.group(1)

    if match3:
        proprieteDataDict['propriete'] = match3.group(1)

    if not match and not match2 and not match3:
        return None

    else:
        return proprieteDataDict


def splitListByKeywords(lst):
    sublists = []
    sublist = []
    for item in lst:
        if any(keyword.lower() in item.lower() for keyword in KEYWORDSDESIGNATION):
            if sublist:
                sublists.append(sublist)
                sublist = []
        sublist.append(item)
    if sublist:
        sublists.append(sublist)
    return sublists


class ReferenceCadastrale:
    def __init__(self, section, numero, nature, lieuDit, surface):
        self.section = section
        self.numero = numero
        self.nature = nature
        self.lieuDit = lieuDit
        self.surface = surface


class Propriete:
    def __init__(self, proprieteDict):
        self.numero = proprieteDict['propriete']
        self.departement = proprieteDict['departement']
        self.commune = proprieteDict['commune']
        self.referencesCadastrales = []

    def appendReferenceCadastrale(self, referenceCadastrale):
        self.referencesCadastrales.append(referenceCadastrale)


class Proprietaire:
    def __init__(self, rawNom, dateNaissance, titre, adresse):
        self.rawNom = rawNom
        self.dateNaissance = dateNaissance
        self.proprietes = []
        self.titre = titre
        self.adresse = adresse

    def formatNom(self, nom):
        nomTemp = nom.replace('Madame', '').replace('Monsieur', '').strip()
        nom = nomTemp.split()[0].strip()
        prenoms = nomTemp.replace(nom, '').strip()
        return nom, prenoms

    def appendPropriete(self, propriete):
        self.proprietes.append(propriete)


class Proprietaires:
    def __init__(self):
        self.list = []

    def append(self, rawNom, dateNaissance, titre, adresse):
        for proprietaire in self.list:
            if proprietaire.rawNom == rawNom and proprietaire.dateNaissance == dateNaissance:
                return proprietaire
        self.list.append(Proprietaire(rawNom, dateNaissance, titre, adresse))
        return self.list[-1]


class Parser:
    @staticmethod
    def getTypeContact(nom):
        # Mots-clés pour identifier les personnes morales publiques
        contact_moral_public = ["COMMUNE", "DEPARTEMENT", "REGION", "ETAT", "COM", "DEP"]

        # Mots-clés pour identifier les personnes morales privées
        contact_moral_prive = ["SA", "SOCIETE ANONYME", "SARL", "SOCIETE", "SAS", "SCI"]

        # Convertir le nom en majuscules pour la recherche insensible à la casse
        nom_upper = nom.upper()

        # Vérification si le nom contient des mots-clés de personne morale publique
        for mot in contact_moral_public:
            if mot in nom_upper:
                return 4

        # Vérification si le nom contient des mots-clés de personne morale privée
        for mot in contact_moral_prive:
            print(mot)
            if mot in nom_upper:
                print("Nom upper")
                print(nom_upper)
                return 3


        return 1


    def __str__(self):
        return "Parser object with {} proprieteBlocks".format(len(self.proprieteBlocks))

    def __init__(self, html_path):
        self.proprietaires = Proprietaires()
        htmltext = open(html_path, 'r', encoding='latin-1').read()
        self.proprieteBlocks = htmltext.split("PROPRIETE 00")[1:]

    def run(self):
        for block in self.proprieteBlocks:
            block = "PROPRIETE 00" + block
            self.extractData(block)
        return self.saveDataToJson()

    def extractCommuneAndDepartement(self, block):
        commune_pattern = r"Commune : (\w+)"
        commune_match = re.search(commune_pattern, block)
        commune = commune_match.group(1) if commune_match else None
        print("Commune :")
        print(commune)

        departement_pattern = r"Département : (\w+)\s*\((\d+)\)"
        departement_match = re.search(departement_pattern, block)
        if departement_match:
            departement = {
                "nom": departement_match.group(1),
                "code": departement_match.group(2)
            }
        else:
            departement = {"nom": None, "code": None}

        print("Département :")
        print(departement)

        return commune, departement

    def extractData(self, block):
        proprieteDict = extractPropriete(block)
        proprietairePart = block.split("DESIGNATIONS DES PROPRIETAIRES OU PRESUMES TELS")[1].split("ORIGINE DE PROPRIETE")[0]
        readableProprietairePart = makeHTMLreadable(proprietairePart)
        parts = [part.replace("\n", "").strip() for part in readableProprietairePart.split('|') if part.strip() != '']
        propriosData = splitListByKeywords(parts)

        for proprioData in propriosData:
            titre = proprioData[0]
            nom = proprioData[1]
            dateDeNaissance = 'empty'
            adresse = 'empty'

            for champ in proprioData:
                if "né le" in champ or "née le" in champ:
                    dateDeNaissance = extractDateOfBirth(parts[2])
                if "demeurant" in champ or "née le" in champ:
                    adresse = champ.replace("demeurant", "").strip()

            proprio = self.proprietaires.append(nom, dateDeNaissance, titre, adresse)

            referencesCadastrales = self.extractReferencesCadastrales(block)

            propriete = Propriete(proprieteDict)
            for referenceCad in referencesCadastrales:
                propriete.appendReferenceCadastrale(referenceCad)
            proprio.proprietes.append(propriete)

    def extractReferencesCadastrales(self, block):
        referencesCadastrales = []
        referencePartBrut = block.split("Références cadastrales")

        if len(referencePartBrut) > 1:
            referencePartBrut = referencePartBrut[1].split('Surface (m²)')

            if len(referencePartBrut) > 1:
                referencePartClean = makeHTMLreadable(referencePartBrut[-1])
                parts = [part.replace("\n", "").strip() for part in referencePartClean.split('|') if
                         part.strip() != '']

                pointeur = 0
                while pointeur < len(parts) - 4:
                    section = parts[pointeur]
                    numero = int(parts[pointeur + 1])
                    nature = parts[pointeur + 2]
                    lieuDit = parts[pointeur + 3]
                    surface = int(parts[pointeur + 4].replace(" ", ""))
                    referencesCadastrales.append(ReferenceCadastrale(section, numero, nature, lieuDit, surface))
                    pointeur += 5

                return referencesCadastrales

    def separer_noms_prenoms(self, chaine):
        pattern = r'([A-ZÉÈÊËÀÂÄÔÖÎÏÛÜÇ\-]+(?: [A-ZÉÈÊËÀÂÄÔÖÎÏÛÜÇ\-]+)*) (.+)'
        matches = re.findall(pattern, chaine)

        noms = []
        prenoms = []

        for match in matches:
            nom, prenom = match
            noms.append(nom)
            prenoms.append(prenom.strip())

        return noms, prenoms

    def saveDataToJson(self):
        donnees_parcelles = {"Parcelles": []}

        # commune, departement = None, None

        for proprietaire in self.proprietaires.list:
            adresse_parts = proprietaire.adresse.split()
            noms, prenoms = self.separer_noms_prenoms(proprietaire.rawNom)

            for _, propriete in enumerate(proprietaire.proprietes):
                for referenceCadastrale in propriete.referencesCadastrales:
                    type_contact = self.getTypeContact(proprietaire.rawNom)
                    # if commune is None or departement is None:
                    #     commune, departement = self.extractCommuneAndDepartement(block)

                    parcelle = {
                        "NOM": noms,
                        "PRENOM": prenoms,
                        "AN": "",
                        "DEPARTEMENT": propriete.departement,
                        "COMMUNE": propriete.commune,
                        "SECTION": f"{referenceCadastrale.section} {referenceCadastrale.numero}",
                        "N PLAN": propriete.numero,
                        "ADRESSE": proprietaire.adresse.split(',')[0],
                        "CODE": "",
                        "SUPERFICIE": referenceCadastrale.surface,
                        "TYPEID": type_contact
                    }
                    donnees_parcelles["Parcelles"].append(parcelle)

        return donnees_parcelles

    def getProprietes(self, proprietaire):
        data = {}
        for index, propriete in enumerate(proprietaire.proprietes):
            data[str(index)] = {
                'identifiantPropriete': propriete.numero,
                'ReferencesCadastrales': self.getReferencesCadastrales(propriete.referencesCadastrales)
            }
        return data

    def getReferencesCadastrales(self, referencesCadastrales):
        data = {}
        for index, referenceCadastrale in enumerate(referencesCadastrales):
            data[str(index)] = {
                'section': referenceCadastrale.section,
                'numero': referenceCadastrale.numero,
                'nature': referenceCadastrale.nature,
                'lieuDit': referenceCadastrale.lieuDit,
                'surface': referenceCadastrale.surface,
            }
        return data

    def convertToParcelleDict(self, nom, an, section, numero_plan, adresse, code_rivioli):
        parcelle = {
            "NOM": nom,
            "AN": an,
            "SECTION": section,
            "N PLAN": numero_plan,
            "ADRESSE": adresse,
            "CODE": code_rivioli
        }
        return parcelle