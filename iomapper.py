import airspeed
from xml.etree import ElementTree as ET
import sys
import os

class IOMapper:

    def __init__(self):
        self.entities = []
        self.relations = []
        self.OUTPUT_DIR = 'output'


    def generateJava(self, filename):
        self.procesar_xml(filename)
        dtos = self.construirDtos()
        self.procesar_plantilla(dtos)


    def procesar_xml(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        
        elements = root.findall('.//mxCell')

        for element in elements:
            if (self.isEntity(element)):
                self.createEntity(element)

        for element in elements:
            if (self.isRelation(element)):
                self.createRelation(element)


    def findEntityById(self, id):
        for entity in self.entities:
            if entity['id'] == id:
                return entity


    def isRelation(self, element):
        if not self.isDrawioElement(element):
            return False
        styles = element.attrib['style']
        return 'orthogonalEdgeStyle' in styles


    def createRelation(self, element):
        source = self.findEntityById(element.attrib['source'])
        target = self.findEntityById(element.attrib['target'])
        
        type = 'points'
        if 'dashed=1' in element.attrib['style']:
            type = 'extends'

        self.relations.append({
            'source': source,
            'target': target,
            'type': type
        })


    def createEntity(self, element):
        self.entities.append({
            'clazz': element.attrib['value'],
            'id': element.attrib['id'],
            'isAbstract': 'dashed' in element.attrib['style']
        })


    def isEntity(self, element):
        if not self.isDrawioElement(element):
            return False

        styles = element.attrib['style']
        return 'shape=umlEntity' in styles


    def isDrawioElement(self, element):
        try:
            element.attrib['style']
            return True
        except:
            return False


    def procesar_plantilla(self, dtos):

        with open('class.vm', 'r') as template_file:
            template_content = template_file.read()

        template = airspeed.Template(template_content)

        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)
            
        for dto in dtos:
            output = template.merge(dto)
            self.exportar_fichero(dto, output)


    def exportar_fichero(self, dto, output):
        filename = dto['clazz']['name'] + '.java'
        with open(self.OUTPUT_DIR + '/' + filename, 'w') as java_file:
            java_file.write(output)


    def findExtends(self, entity):
        for relation in self.relations:
            if relation['type'] == 'extends':
                if relation['source']['id'] == entity['id']:
                    return relation['target']['clazz']
        return ''


    def findAttributes(self, entity):
        attributes = []
        for relation in self.relations:
            if (relation['type'] == 'points'):
                if relation['source']['id'] == entity['id']:
                    attributes.append({
                        'clazz': relation['target']['clazz'],
                        'name': relation['target']['clazz'].lower(),
                        'toUpperCase': relation['target']['clazz'].upper()
                    })
        return attributes


    def findIsBase(self, entity):
        for relation in self.relations:
            if relation['type'] == 'extends':
                if relation['target']['id'] == entity['id']:
                    return True
        return False


    def construirDtos(self):
        dtos = []
        for entity in self.entities:
            dtos.append({
                'clazz': {
                    'name': entity['clazz'],
                    'extends': self.findExtends(entity),
                    'isAbstract': entity['isAbstract'],
                    'isBase': self.findIsBase(entity),
                    'attributes': self.findAttributes(entity)
                }
            })
        return dtos


filename = sys.argv[1]
ioMapper = IOMapper()
ioMapper.generateJava(filename)