cp ../LICENSE .
cp -R ../docs/ ./docs
cp -R ../indy_community_demo/indy_community/ ./indy_community

python setup.py sdist
