# What is the GT Installer?

The GT Installer is a Composer script which automatically gathers Drupal 11, the GT Profile, the GT Theme, the GT Tools module, and a couple third-party modules upon which the theme relies.

There are a number of files in the installer -- most of them are boilerplate, but if you're interested in customizing the installer for your own nefarious purposes (say, for example, you have a custom module you want to be installed on all your sites), you will want to modify the composer.json file.

# What is Composer?

Composer is a PHP dependency manager. It is quite possible to install Drupal 11 without it, but doing so presents serious issues. If you look in the vendor directory belonging to a typical Drupal 11 site, you will see as many as fifty independent PHP libraries and utilities, Twig not least among them (that's right -- Twig is not an integral part of Drupal, rather it is a third-party system).

Drupal relies heavily upon these projects, and in many cases they rely upon one another. If one of them is out of date, you could simply download a newer version, but since there are often multiple interdependencies, doing so can lead to incompatibilites. So before updating any vendor projects, it is incumbent upon the site owner to check whether Drupal or any of those other (fifty plus) projects will be happy with the new version.

Needless to say, this is a recipe for frustration. Fortunately, we have Composer, which does all of this version checking automatically.

Composer has some big negatives: it's slow and extremely memory-hungry. It's also somewhat confusing and frustrating to use occasionally. We recognize these shortcomings, but the alternative -- a broken website whose issues cannot be diagnosed without understanding how Sebastian or Fabpot works -- is untenable. We're doing what we can to alleviate Composer's failings with this installer package.

# What is the GT Profile?

The installer can't do everything on its own. Specifically, it gathers the components for a GT Drupal 11 site, but does nothing with them. "Installer" might, in fact be something of a misnomer, because it's Drush that does the actual installation -- creating all the database tables and configuring the new website. Drush processes the Drupal install using the GT Profile as a guide.

You can install your site manually, but if you're using the GT Theme, you will need to manually turn it on and remember to enable the GT Tools module as well. Please note that Curie blocks and settings will not be installed using this method.

# Contact us

We hope you've enjoyed this mass of words and we now return you to your regularly scheduled programming.

Contact webteam@gatech.edu for any major questions or more information.
