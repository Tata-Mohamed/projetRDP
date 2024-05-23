import re
import json

KEYWORDSDESIGNATION=["propriétaire","usufruitier",'Usufruitière']

def makeHTMLreadable(html):
    clean_text = re.sub(r'<[^>]*>', '|', html)
    while "&nbsp;" in clean_text:
        clean_text=clean_text.replace('&nbsp;'," ")
    return clean_text

def extractDateOfBirth(text):
    text=text.replace("née","né")
    pattern = r'né\s+le\s+(\d{2}/\d{2}/\d{4})'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return "empty"

def extractPropriete(text):
    pattern = r"PROPRIETE\s(\d{3,10})"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None

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
    def __init__(self,section,numero,nature,lieuDit,surface):
        self.section=section
        self.numero=numero
        self.nature=nature
        self.lieuDit=lieuDit
        self.surface=surface

class Propriete:
    def __init__(self,numero):
        self.numero=numero
        self.referencesCadastrales=[]

    def appendReferenceCadastrale(self,referenceCadastrale):
        self.referencesCadastrales.append(referenceCadastrale)

class Proprietaire:
    def __init__(self,rawNom,dateNaissance,titre,adresse):
        self.rawNom=rawNom
        # self.nom,self.prenoms=self.formatNom(rawNom)
        self.dateNaissance=dateNaissance
        self.proprietes=[]
        self.titre=titre
        self.adresse=adresse

    def formatNom(self,nom):
        nomTemp=nom.replace('Madame','').replace('Monsieur','').strip()
        nom=nomTemp.split()[0].strip()
        prenoms=nomTemp.replace(nom,'').strip()
        return nom,prenoms

    def appendPropriete(self,propriete):
        self.proprietes.append(propriete)

class Proprietaires:
    def __init__(self):
        self.list=[]

    def append(self,rawNom,dateNaissance,titre,adresse):
        for proprietaire in self.list:
            if proprietaire.rawNom==rawNom and proprietaire.dateNaissance==dateNaissance:
                return proprietaire
        self.list.append(Proprietaire(rawNom,dateNaissance,titre,adresse))
        return self.list[-1]

class Parser:
    def __init__(self, html_file):
        self.proprietaires=Proprietaires() #objet proprietaireS pour gerer plus facilement les append
        htmltext=open(html_file,'r', encoding='latin-1').read()
        self.proprieteBlocks=htmltext.split("PROPRIETE 00")[1:]

    def run(self):
        for block in self.proprieteBlocks:
            block="PROPRIETE 00"+block
            self.extractData(block)
            # break
        # self.displayData()
        self.saveDataToJson()


    def extractData(self,block):
        proprieteNumber=extractPropriete(block)
        proprietairePart=block.split("DESIGNATIONS DES PROPRIETAIRES OU PRESUMES TELS")[1].split("ORIGINE DE PROPRIETE")[0]
        readableProprietairePart=makeHTMLreadable(proprietairePart)
        parts = [part.replace("\n","").strip() for part in readableProprietairePart.split('|') if part.strip() != '']
        propriosData=splitListByKeywords(parts)
        for proprioData in propriosData:
            titre=proprioData[0]
            nom=proprioData[1]
            dateDeNaissance='empty'
            adresse='empty'

            for champ in proprioData:
                if "né le" in champ or "née le" in champ:
                    dateDeNaissance=extractDateOfBirth(parts[2])
                if "demeurant" in champ or "née le" in champ:
                    adresse=champ.replace("demeurant","").strip()


            proprio=self.proprietaires.append(nom,dateDeNaissance,titre,adresse)  #ici on recupere l'objet proprio concerné

            referencesCadastrales=self.extractReferencesCadastrales(block)

            propriete=Propriete(proprieteNumber)
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



    def saveDataToJson(self):
            data = {}
            for index,proprietaire in enumerate(self.proprietaires.list):
                data[str(index)] = {
                    'nom':proprietaire.rawNom,
                    'titre': proprietaire.titre,
                    'dateNaissance': proprietaire.dateNaissance,
                    'adresse': proprietaire.adresse,
                    'proprietes': self.getProprietes(proprietaire)
                }
            # with open('donnes_rdp1.json', 'w', encoding='utf-8') as json_file:
            #     json.dump(data, json_file, indent=4, ensure_ascii=False)

            return json_file

    def getProprietes(self,proprietaire):
        data={}
        for index,propriete in enumerate(proprietaire.proprietes):
            data[str(index)] = {
                'identifiantPropriete':propriete.numero,
                'ReferencesCadastrales':self.getReferencesCadastrales(propriete.referencesCadastrales)
            }
        return data

    def getReferencesCadastrales(self,referencesCadastrales):
        data={}
        for index,referenceCadastrale in enumerate(referencesCadastrales):
            data[str(index)] = {
                'section':referenceCadastrale.section,
                'numero':referenceCadastrale.numero,
                'nature':referenceCadastrale.nature,
                'lieuDit':referenceCadastrale.lieuDit,
                'surface':referenceCadastrale.surface,
            }
        return data

    def displayData(self):
        for proprietaire in self.proprietaires.list:
            print(proprietaire.titre)
            print(proprietaire.rawNom)
            if proprietaire.dateNaissance!="empty":
                print(proprietaire.dateNaissance)
            if proprietaire.adresse!="empty":
                print(proprietaire.adresse)
            for propriete in proprietaire.proprietes:
                print("-"+propriete.numero)
            print("_________________________________________________")
