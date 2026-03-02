#!/usr/bin/env bash

### Options ###
while getopts d:t option
do
case "${option}"
in
d) PROJECTPATH=${OPTARG};;
t) DRYRUN=true;;
esac
done



### Project path? ###
if [ -z "$PROJECTPATH" ]; then
	echo -n "Enter the full path to your project's root directory: "
	read -e PROJECTPATH
fi

cd $PROJECTPATH



### Uninstall incompatible modules ###
echo
echo "Uninstalling incompatible modules."

# Got to do this ridiculous dance because hashes don't exist in Bash 3
blocklist=(
  'Advanced Aggregation'
	'Bulk Author Update'
  'Menus Attribute'
	'Transliterate Filenames'
  'Google Analytics'
  'Color'
  'CKEditor'
  'Classy'
  'Seven'
	'Matomo Tagmanager'
	'Quick Edit'
	'Block Content Permissions'
	'Custom Search'
  'Video Filter'
)
blocklist_keys=(
  'advagg'
	'bulk_author_update'
  'menus_attribute'
	'transliterate_filenames'
  'google_analytics'
  'color'
  'ckeditor'
  'classy'
  'seven'
	'matomo_tagmanager'
	'quickedit'
	'block_content_permissions'
	'custom_search'
  'video_filter'
)

# List 'em
echo
echo 'The following modules are currently incompatible with Drupal 11.';
echo 'If any of them provide needed functionality for your site, you';
echo 'will need to find a workaround or wait until the module is updated.'
echo
delim=""
for item in "${blocklist[@]}"; do
  echo "$delim$item"
done

# Ax the user what he/she/they/y'all want to do with 'em.
echo
echo
read -r -p "Continue? [Y/n] " response
case "$response" in
    [nN][oO]|[nN])
      echo 'Exiting.'
      exit 1
      ;;
esac

# PMU those modules
for i in ${!blocklist_keys[@]}; do
  enabled=$(drush pml | grep ${blocklist_keys[$i]} | grep "Enabled")
  if [ ! -z "$enabled" ]; then
    echo "Uninstalling incompatible module: ${blocklist[$i]}"
    drush pmu ${blocklist_keys[$i]}
  fi
done



### Remove composer lock file ###
if test -f "composer.lock"; then
  echo "Removing composer lock file."
  rm composer.lock
fi



### Remove incompatible modules from manifest ###
echo
echo "Removing incompatible module entries from composer.json."
for i in ${!blocklist_keys[@]}; do
  installed=$((composer show --ansi "drupal/${blocklist_keys[$i]}") 2>&1)
  if [[ $installed != *"not found"* ]]; then
    echo "Removing ${blocklist[$i]}"
    composer remove --ansi "drupal/${blocklist_keys[$i]}" --no-update
  fi
done



### Update module constraints ###
echo
echo "Updating module constraints for D11 compatibility."

# More Bash 3 compatiblity workarounds
declare modules=(
  "drupal/anchor_link"
  "drupal/better_exposed_filters"
	"drupal/book"
  "drupal/cas"
  "drupal/computed_field"
  "drupal/convert_bundles"
  "drupal/core-composer-scaffold"
  "drupal/core-project-message"
  "drupal/core-recommended"
	"drupal/ctools"
	"drush/devel"
  "drush/devel_entity_updates"
  "drush/double_field"
  "drush/drush"
  "drupal/editor_file"
  "drupal/entity_type_clone"
  "drupal/exclude_node_title"
  "drupal/faqfield"
	"drupal/file_delete"
	"drupal/google_tag"
  "drupal/hierarchical_taxonomy_menu"
	"drupal/iframe"
  "drupal/iframe_title_filter"
  "drupal/inline_block_title_automatic"
  "drupal/inline_entity_form"
  "drupal/jquery_ui_datepicker"
  "drupal/layout_builder_restrictions"
	"drupal/linkit"
  "drupal/mailchimp"
  "drupal/matomo"
  "drupal/media_entity_file_replace"
  "drupal/menu_link_attributes"
	"drupal/metatag"
  "drupal/mimemail"
	"drupal/module_filter"
  "drupal/nodeaccess"
	"drupal/protected_file"
  "drupal/rdf"
	"drupal/stage_file_proxy"
  "drupal/styleguide"
	"drupal/taxonomy_term_depth"
	"drupal/twig_tweak"
	"drupal/typed_data"
  "drupal/video_embed_field"
	"drupal/views_autocomplete_filters"
  "drupal/views_block_area"
  "drupal/views_taxonomy_term_name_into_id"
  "drupal/xmlsitemap"
  "drupal/youtube"
  "gt/gt_profile"
  "gt/gt_theme"
  "gt/gt_tools"
  "gt/hg_reader"
)
declare constraints=(
  "3.0"         # anchor_link
  "7.0"         # better_exposed_filters
	"2.0"       	# book
  "3.0@beta"    # cas
  "4.0@beta"    # computed_field
  "3.0@alpha"   # convert_bundles
  "11.0"        # core-composer-scaffold
  "11.0"        # core-project-message
  "11.0"        # core-recommended
	"4.0"					# ctools
	"5.3"					# devel
  "4.2"         # devel_entity_updates
  "5.0@beta"    # double_field
  "13.0"        # drush
  "2.0@RC"      # editor_file
  "4.0"         # entity_type_clone
  "2.0@alpha"   # exclude_node_title
  "8.0"         # faqfield
	"3.0"					# file_delete
	"2.0"					# google_tag
  "3.0@alpha"   # hierarchical_taxonomy_menu
	"3.0"					# iframe
  "3.0"         # iframe_title_filter
  "2.0"         # inline_block_title_automatic
  "3.0@RC"      # inline_entity_form
  "2.1"         # jquery_ui_datepicker
  "3.0"         # layout_builder_restrictions
	"7.0"					# linkit
  "3.0"         # mailchimp
  "2.0@alpha"   # matomo
  "1.3"         # media_entity_file_replace
  "1.5"         # menu_link_attributes
	"2.1"					# metatag
  "2.0"         # mimemail
	"5.0"					# module_filter
  "2.0@alpha"   # nodeaccess
	"2.0"					# protected_file
  "3.0@beta"    # rdf
	"3.0"					# stage_file_proxy
  "2.0"         # styleguide
	"3.0"					# taxonomy_term_depth
	"3.4.0"  	    # twig_tweak
	"2.1"					# typed_data
  "3.0@beta"    # video_embed_field
	"2.0"		      # views_autocomplete_filters
  "2.0@RC"      # views_block_area
  "1.0"         # views_taxonomy_term_name_into_id
  "2.0"         # xmlsitemap
  "3.0@beta"    # youtube
  "5.0"         # gt_profile
  "5.0"         # gt_theme
  "5.0"         # gt_tools
  "5.0"         # hg_reader
)

for u in ${!modules[@]}; do
  installed=$((composer show --ansi "${modules[$u]}") 2>&1)
  if [[ $installed != *"not found"* ]]; then
    echo "Updating ${modules[$u]}"
    if [[ ${modules[$u]} == *'gt_editor'* ]]; then
      composer require --ansi "${modules[$u]}: ${constraints[$u]}" --no-update
    else
      composer require --ansi "${modules[$u]}:^${constraints[$u]}" --no-update
    fi
  fi
done



### Install ###
echo
echo "Installing Drupal 11 and dependencies."

# discard changes
COMPOSER_DISCARD_CHANGES=true

if [ "$DRYRUN" = true ]; then
  installation=$((composer update --dry-run --no-interaction --ansi --with-all-dependencies) 2>&1 | tee /dev/tty)
else
  installation=$((composer update --no-interaction --ansi --with-all-dependencies) 2>&1 | tee /dev/tty)
fi
if [[ "$installation" == *"Your requirements could not be resolved to an installable set of packages."* ]]; then
  echo "As you can see, composer is not happy about something. Most likely your installation includes a module that we haven't anticipated. Please copy the error message above and send it to webteam@gatech.edu."
  echo
  exit 1
fi



### DB update ###
echo
echo "Updating database."
drush updb



### DONE ###
echo
echo "Finished."

echo
echo "IMPORTANT: Before proceeding, make sure ALL of the following modules are UNINSTALLED from your production site:"
delim=""
for item in "${blocklist[@]}"; do
  echo "$delim$item"
done
echo

echo "Once this is done, you may commit your files and run update.php. Most sites will WSOD until update.php is run; don't be frightened."
