openapi-generator:
	curl -L https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/4.2.2/openapi-generator-cli-4.2.2.jar > openapi-generator

generate: openapi-generator
	yq .Resources.Api.Properties.DefinitionBody < ../templates/api.yml > swagger.packaged.json
	java -jar openapi-generator generate \
		-g python \
		-i ./swagger.packaged.json \
		-o ./build/ \
		-c ./config.json
	pip install ./build/
