swagger-server:
	live-server . &
	nodemon --watch ../templates/api.yml --exec 'yq .Resources.Api.Properties.DefinitionBody < ../templates/api.yml > spec.json'
