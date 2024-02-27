from featuremanagement._models._feature_flag import FeatureFlag
import json
test = '{"id" : "Alpha", "enabled": true, "conditions":{}, "allocation":{"default_when_enabled": false}}'
json_obj = json.loads(test)
ff = FeatureFlag.convert_from_json(json_obj)

print(type(ff))
print(type(ff.allocation))
print(ff.allocation.default_when_enabled)