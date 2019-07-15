# Project - Item Catalog
## Udacity Full Stack Nano Degree  

## About

This project implements a list of items within a variety of categories, and integrates third party 
user registration and authentication.  In addition, the application offers a simple
user + password authentication as well.  The third party authentication used is by way 
of google.  

Any user can view categories and items, however in order to add, modify or delete, the 
user must be authenticated.  In addition, in order to modify or delete a category,
the user must be the owner / creator of the item.  

Some of the technologies used in this application include:
* Flask 
* Bootsrap
* Jinja2
* SQLite

---

## Installation and execution
In order to install and execute, download or install the following:
* [Virtual Box](https://www.virtualbox.org/wiki/Downloads)
* [Install vagrant](https://www.vagrantup.com/)
* [Clone this repository](https://github.com/jcarter62/udacity-item-catalog.git)
---
* open a command line and change current directory to where you cloned the repository.
* perform _vagrant up_, and wait for a command prompt to return.
* perform _vagrant ssh_
* cd /vagrant/catalog
* execute _python app.py_
* open browser, and visit http://localhost:8000
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
- /api/v1/categories/*category-name* <br>Returns one category where name=*category-name* record if found.
- /api/v1/items<br>Returns a list of all items in database.
- /api/v1/items/*item-id*<br>Returns one item record where item id=*item-id*.










