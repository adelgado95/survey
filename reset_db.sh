sudo docker exec survey-mysql mysql -u root -e "drop database if exists survey"
sudo docker exec survey-mysql mysql -u root -e "create database survey"
sudo docker exec survey-mysql mysql -u root -e " CREATE USER 'survey'@'localhost' IDENTIFIED BY 'survey'"
sudo docker exec survey-mysql mysql -u root -e "GRANT ALL PRIVILEGES ON survey.* TO 'survey'@'localhost';"
