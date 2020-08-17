from ruamel import yaml

class Yaml_Tool:
    def __init__(self):
        pass

    def getValue(self, yamlPath):
        with open(yamlPath) as yamlFile:
            content = yaml.load(yamlFile, Loader=yaml.RoundTripLoader)
            yamlFile.close()
            return content

    def saveParam(self,yamlPath,param):
        with open(yamlPath, 'w') as yamlFile:
            yaml.dump(param, yamlFile, Dumper=yaml.RoundTripDumper)
            yamlFile.close()

if __name__ == '__main__':
    yamlTool=Yaml_Tool()
    print(yamlTool.getValue("configure.yaml")["IO"]["bench3_io"])