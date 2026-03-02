**Drupal 11 Manual Upgrade Instructions**

(Thanks to Michael Barnwell for documenting this process.)

- Document the settings for all views on your website
- Put your site in Maintenance Mode.
- Clear cache, then logout.
- In Plesk, download a dump of the database. Then create a Plesk backup.

**Perform the GT Updates first, and test your site, before doing the D11 upgrade**

- Update the Composer.json file to use the version 5 of all the GT modules:

`"gt/gt\_profile": "^5.0",` \
`"gt/gt\_theme": "^5.0",` \
`"gt/gt\_tools": "^5.0",` \
`"gt/hg\_reader": "^5.0”,`

- In Plesk, go to PHP Composer and run Update. 
- After the update is completed, login to your website and run update.php. There were no updates, but you should always run this after an update. Other modules could have been updated also.
- Test your site. I found that the Theme update moved the Breadcrumbs to below the Page Name. If this happens, change the order on the Block Layout page.
- Also, some of the settings for my Views were changed by the Theme update. For example, the ‘Height Style’ and a couple of other settings were changed.
- Uninstall the following modules:
- ‘Color’, ‘RDF’, ‘QuickEdit’
- Change the setting for the Admin Theme to use the ‘Default’ Theme, and then uninstall the ‘Seven’ theme. 

NOTE:
The ‘Seven’ theme is being removed from Core, but you can add the Contrib module to your Composer file and use it in D11 or use the ‘Clario’ theme as the Admin Theme which is in Core.  

If you want to use the ‘Seven’ theme in D11, take screenshots of the current Block Layout for the Seven theme.  The contrib module will change this configuration and you will have to correct it after the upgrade.  See the Appendix at the bottom of these instructions for more details.

- Clear cache and logout of your site.
- Create an extra backup of the composer.json file.

**D11 Upgrade**

- Review the IC Drupal 11 Upgrade Instructions beginning with the Manual Upgrade Process section.

<https://github.gatech.edu/ICWebTeam/webteam/blob/master/D11%20Upgrade%20Guide.md>

- Take this into consideration when updating your Composer.json file. You may have some modules which I did not have, so they are not discussed in these instructions.
- In Plesk, download a dump of the database. Then create a Plesk backup.
- Backup your composer.json and composer.lock files.

**Make the following changes to your composer.json file:**

Core upgrade/Update these to version 11:

`"drupal/core-composer-scaffold": "^11.0"` \
`"drupal/core-project-message": "^11.0"` \
`"drupal/core-recommended": "^11.0"`

- Add contrib modules for Core module replacements:

`"drupal/externalauth": "^2.0"` \
`"drupal/jquery\_ui\_accordion": "^2.0"` \
`"drupal/stable”: "^2.0",` \
`"drupal/seven”: "^1.0"` (If you want to use it for the Admin Theme in D11)

- In Plesk, on the PHP Composer page, run Update.
- If there are no dependency errors, you can proceed with the steps below:

- You will need to run update.php on your site.  Since you are not logged into your website, you will need to change the ‘update\_free\_access’ value in the settings.php file from ‘FALSE’ to ‘TRUE’ so you can run update.php for your site. Remember to change this back to ‘FALSE’ after completing the D11 upgrade. You will need to change the permissions on the settings.php file to ‘0600’ so you can edit it.  Remember to set the permissions back to ‘0400’ when you are done.
- Once you have changed this to ‘TRUE’ and saved the file, navigate to your website and run update.php.
- Your site will show an error message until you run this and perform the database updates.

If update.php is successful:

- Test your site.  Make corrections to things that the upgrade may have changed incorrectly.
- Go to the **Appearance** page and select an Admin Theme.  If you choose the ‘Seven’ theme, see the Appendix below concerning configuration changes you will need to make.
- If all is well, clear cache and make another backup of your site.
- Take your site out of Maintenance Mode and clear cache.
- Set the ‘update\_free\_access’ value back to ‘FALSE’ in the settings.php file, and set the permissions on the file back to ‘0400’ (Owner Read only).

**Appendix**

If you enable the ‘Seven’ contrib theme as the Admin Theme, you will notice that each page which uses the theme shows many links and items before showing the main page fields.  You will need to change the Block Layout for the Seven theme to correct this.

**Changes to Seven Block Layout Needed**

In the Header: Move ‘Page Title’ to after Breadcrumbs.

Disable: Site Name, Banner Quick Links, Search, Main Navigation, and all Footer and all GT Official Links blocks, and any other blocks which are not needed on your Admin pages.

When you are done, your Block Layout should have the following blocks enabled in the regions specified below, unless you want to reorder differently:

Header Region

Pre-Content and Breadcrumb regions are blank

Remaining Regions

**Clear cache.**
