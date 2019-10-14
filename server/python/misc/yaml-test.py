
import yaml

with open('secrets.yaml') as secretsfile:
    secrets = yaml.load(secretsfile, Loader = yaml.FullLoader)

print(secrets)
print(secrets['mqtt']['username'])
