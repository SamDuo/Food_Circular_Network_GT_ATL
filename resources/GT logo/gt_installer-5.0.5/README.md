# Prerequisites

1) PHP 8.1+
2) [Composer](https://getcomposer.org/)

Composer is a memory hog. You will likely need to set a high(er) memory_limit in your php.ini file.

You will also need to store your GitHub credentials in Composer's authentication store, thus:

`composer -g config http-basic.github.gatech.edu username password`

# Install process

1) Download and unzip the gt_installer (this repo).
2) At the command line, navigate to the gt_installer directory.
3) Make sure the file 'install.sh' is executable.
4) Do `./install.sh` and follow the prompts.

# Command flags

There are several command flags you can use if you don't want to keep entering redundant information on multiple installs or whatever. 

-d : **Project path**. The fully qualified path to your project from the server root
-n : **Database name**. The name of the database. Note that any data in the database will be overwritten.
-u : **Database user**. The database username
-h : **Database host**. The database host (e.g. localhost) for containerized environments use 127.0.0.1.
-r : **Database port**. The database port (e.g. 3306 or 8889)
-s : **Site name**. The site name (e.g. Office of Officework). This will go in the top banner of the site.
-e : **Email**. The site email address
-p : **Profile** The profile you want installed (e.g. developer, builder, communicator)
-l : **Local**. Set this flag to install with a loose (e.g. 777) set of files permissions.

# Manual installation
Alternately, you can do the install process manually:

3) After step 2 above, do `composer create-project --repository-url=packages.json --remove-vcs gt/gt_installer {path-to-your-project-directory}`
5) Do `cd {path-to-your-project-directory}`
6) Do `drush site-install {profile} --db-url=mysql://{username}:{password}@{database-host}/{database} --site-name="{Your Site Name}" --account-mail={your-email@gatech.edu}`

Note that the profile name (developer, builder, communicator) must be prefixed with "gt_" if you are installing manually, e.g. _gt_developer_, _gt_builder_, _gt_communicator_.

## Note for users with 2FA on GitHub

If you use two-factor authentication for your GitHub account, you will need to generate an access token. Instructions can be found here: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line. The token must be made available to composer thusly:

`composer config -g github-oauth.github.gatech.edu paste-your-token-here`

At this time Institute Communications cannot offer support for this feature, but we'll be happy to include revisions to the above documentation if any of it proves to be incorrect.

+++

After installation is complete, you may need to update you Drupal core.

Please report any issues with the installer at https://github.gatech.edu/ICWebTeam/gt_installer/issues
