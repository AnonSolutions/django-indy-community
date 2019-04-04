rm -rf dist
rm -rf django_indy_community.egg-info

cp ../LICENSE .
cp -R ../docs/ ./docs
cp -R ../indy_community_demo/indy_community/ ./indy_community

python setup.py sdist

rm LICENSE
rm -rf ./docs
rm -rf ./indy_community

