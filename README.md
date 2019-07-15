# Project - Item Catalog
### Udacity Full Stack Nano Degree - Project #4  

## About
This project implements a catalog containing categories and associated items.  The application provides two methods provide authentication.  The first method is through a third-party provider.  The second method is by way of a simple user + password local method.  The third-party authentication used is by way of google.  

Any user can view categories and items; however, to add, modify, or delete, the user must be authenticated.  Also, to modify or delete a category, the user must be the owner/creator of the item.  

Some of the technologies used in this application include:
* Flask 
* Bootsrap
* Jinja2
* SQLite

## Prerequisites
In order to install and execute, download or install the following:
* [Virtual Box](https://www.virtualbox.org/wiki/Downloads)
* [Install vagrant](https://www.vagrantup.com/)
* [Clone this repository](https://github.com/jcarter62/udacity-item-catalog.git)

## Installing
* Clone the repository listed above
* open a command line and change current directory to where you cloned the repository.
* perform _vagrant up_, and wait for a command prompt to return.
* perform _vagrant ssh_
* cd /vagrant/catalog
* execute _python app.py_
* open browser, and visit [http://localhost:8000](http://localhost:8000)
* if first time running, login in order to add categories or items.

## Walkthrough Images

Startup<br>
Notice no add category or item buttons, because user is not logged in.
<img src="images/0-startup.png">

Login
<img src="images/1-login.png">

Google Auth dialog if user chooses google login method.
<img src="images/2-google-auth.png">

Home/Startup dialog after login completed.  Notice the buttons available and the user's name and image.
<img src="images/3-home-after-login.png">

Add Category
<img src="images/4-add-category.png">

Add Item1
<img src="images/5-add-item1.png">

Add Item2
<img src="images/5-add-item2.png">

Item List
<img src="images/6-item-list.png">

Logout Dialog
<img src="images/7-logout.png">

Item Modification Limit when user is not logged in
<img src="images/8-item-modification-limit.png">

Item Edit Dialog
<img src="images/9-item-edit.png">

Item Save Dialog
<img src="images/A-item-save.png">

Item Delete Dialog
<img src="images/B-item-delete.png">

## Available API calls
There are 3 main api endpoints available to users.
- /api/v1/catalog: <br>This returns a list of categories and associated items.
- /api/v1/categories <br>This returns a list of all categories.  
- /api/v1/categories/**category-name** <br>Returns one category where name=**category-name** record if found.
- /api/v1/items<br>Returns a list of all items in database.
- /api/v1/items/**item-id**<br>Returns one item record where item id=**item-id**.

## Authors
Jim Carter

## License
This project is licensed under the MIT License

