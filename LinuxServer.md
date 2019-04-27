## Grader Info
IP: 52.221.248.5
SSH Port: 2200

## Steps to configure the server
#### 1.Updating existing package
```
sudo apt-get update
sudo apt-get upgrade
```
#### 2.Security configuration
Allow requests at port 2200
```
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 2200/tcp
sudo ufw allow www
sudo ufw allow ntp
sudo ufw allow 123/udp
sudo ufw enable
```
#### 3. Create User Grader
```
sudo adduser grader
# Give sudo permission
sudo nano /etc/suders.d/grader
```
Add  `grader ALL=(ALL) ALL` in the file.
#### 4. Install necessary packages
```
sudo apt-get install apache2
sudo apt-get install libapachi2-mod-wsgi
sudo apt-get install postgres
```

#### 5.Setting up the database
```
psql
# In the psql shell run the following
create user catalog with password 'library';
create database catalog with owner catalog;
```
#### 6. Colone git app and configure the project to run in server
```
cd /var/www/
sudo mkdir catalog
git clone https://github.com/siam923/Library-Catalog-App
cd catalog/Library-Catalog-App
nano catalog.wsgi
```
Now add the following python code in wsgi file
```
import sys
sys.path.insert(0, 'var/www/catalog/Library-Catalog-App')
from application import app
```
Add conf file for the catalog app
```
sudo nano /etc/apache2/sites-available/catalog.conf
```
Insert the following code in the file
```
<VirtualHost *:80>
    ServerName 52.221.248.5

    WSGIScriptAlias / /var/www/catalog/Library_Catalog-App/catalog.wsgi

    <Directory /var/www/catalog/Library_Catalog-App>
        Order allow,deny
        Allow from all
    </Directory>
</VirtualHost>
```
#### 7.Runing the app
Restart apache server
```
sudo service apache2 restart
```

#### Changing Time Zone
`sudo dpkg-reconfigure tzdata`

### Third Party Resources
* Python
* Flask
* SQLAlchemy
* Postgres SQL
* Apache2
* mod-wsgi
