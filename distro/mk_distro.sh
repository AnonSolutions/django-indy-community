rm -rf dist
rm -rf build
rm -rf django_indy_community.egg-info

cp ../LICENSE .
cp -R ../docs/ ./docs
cp -R ../indy_community_demo/indy_community/ ./indy_community
rm -rf indy_community/static

#python setup.py sdist
python setup.py sdist bdist_wheel

rm LICENSE
rm -rf ./docs
rm -rf ./indy_community

