python manage.py loads_orgs ./trustee-org.yml
sleep 5
python manage.py loads_schemas ./imms-schemas.yml 1
sleep 5
python manage.py loads_orgs ./imms-orgs.yml
sleep 5
