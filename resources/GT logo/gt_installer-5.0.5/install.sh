#!/bin/bash

# WARNING: This script is experimental and may fail on your machine. Use with caution.

# Function to display help information
show_help() {
  cat << EOF
  The following options are available:
    -d      The absolute path to your project
    -n      The name of your project database
    -u      The database user
    -t      The database host; defaults to localhost
    -r      The database port; defaults to 3306
    -s      The name of your site; This will appear as the site title.
    -e      The email address for the site.
    -p      The profile you want to install.
    -l      Include this flag if you are establishing a local site and want the
            files directory permissions to be set to 777.
EOF
}


# Function to handle illegal options
handle_illegal_option() {
  echo "Illegal option --$1"
  exit 2
}

# Function to create a directory if it does not exist
create_directory() {
  if [ ! -d "$1" ]; then
    while true; do
      read -r -p "$1 does not exist. Create it? [y/n] " yn
      case $yn in
          [Yy]* ) mkdir -p "$1"; break;;
          [Nn]* ) echo "Exiting."; exit;;
          * ) echo "Please answer yes or no.";;
      esac
    done
  fi
}

# Function to check if a directory is empty
check_empty_directory() {
  find "$1" -name ".DS_Store" -delete
  if [ "$(ls -A "$1")" ]; then
    echo "$1 is not empty. Exiting."
    exit
  fi
}

# Function to start the process
start_process() {
  echo "Starting..."

  # Clear the composer cache!
  composer clearcache

  # Next composer assembles all the site files.
  if ! yes | composer create-project --repository-url=packages.json --remove-vcs gt/gt_installer "$PROJECTPATH"; then
    echo 'A massive error has occurred. Composer was unable to create your project. It was fun while it lasted.'
    exit
  else
    echo 'Project created successfully...'
  fi
}

# Function to install the site
install_site() {
  # Head to the web directory to finish up.
  cd "${PROJECTPATH}" || exit

  # Then Drush installs the database
  if ! yes | "${PROJECTPATH}"${DIRECTORY_SEPARATOR}vendor${DIRECTORY_SEPARATOR}bin${DIRECTORY_SEPARATOR}drush site-install "gt_$PROFILE" --db-url=mysql://"$DBUSER":"$DBPASS"@"$DBHOST":"$DBPORT"/"$DBNAME" --site-name="$SITENAME" --account-mail="$EMAIL"; then
    echo 'A massive error has occurred. Drush failed to install the site. Drush is funny that way.'
    exit
  else
    echo 'Site installed successfully...Remember to copy down your username and password until you change it'
  fi
}

# Function to set permissions
set_permissions() {
  chmod 755 "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default"
  chmod 770 "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}default.services.yml"
  #chmod 644 "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}settings.php"

  if [ "$LOCAL" = true ]; then
    mkdir -p "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}files"
    echo 'Loosening files permissions for local use.'
    find "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}files" -type d -print0 | xargs -0 chmod 777
  else 
    echo 'Tightening files permissions.'
    find "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}files" -type d -print0 | xargs -0 chmod 755
  fi

  find "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}files" -type f -print0 | xargs -0 chmod 644
}

# Function to fix permissions issue
fix_permissions_issue() {
  chmod 644 "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}settings.php"
  echo '' >> "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}settings.php"
  echo '# Skip permissions hardening to prevent Composer Update failure in Plesk environment' >> "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}settings.php"
  echo '$settings['\''skip_permissions_hardening'\''] = TRUE;' >> "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}settings.php"
  chmod 444 "${PROJECTPATH}${DIRECTORY_SEPARATOR}web${DIRECTORY_SEPARATOR}sites${DIRECTORY_SEPARATOR}default${DIRECTORY_SEPARATOR}settings.php"
}

# Parse options
while getopts d:n:u:t:r:s:e:p:-:lh option
do
  if [ "${option}" = "-" ]; then
    OPT="${OPTARG%%=*}"
    OPTARG="${OPTARG#"$OPT"}"
    OPTARG="${OPTARG#=}"

    case "$OPT" in
      h | help )     show_help; exit 0 ;;
      ??* )          handle_illegal_option "$OPT" ;;
      ? )            exit 2 ;;
    esac
  fi

  case "${option}"
    in
      d) PROJECTPATH=${OPTARG};;
      n) DBNAME=${OPTARG};;
      u) DBUSER=${OPTARG};;
      t) DBHOST=${OPTARG};;
      r) DBPORT=${OPTARG};;
      s) SITENAME=${OPTARG};;
      e) EMAIL=${OPTARG};;
      p) PROFILE=${OPTARG};;
      l) LOCAL=true;;
  esac
done

DIRECTORY_SEPARATOR='/'
if [[ $OSTYPE == 'msys' ]]; then
  DIRECTORY_SEPARATOR='\'
fi


# Beginning of the prompts
read -e -r -p "Enter the full path to your project directory: " PROJECTPATH

create_directory "$PROJECTPATH"
check_empty_directory "$PROJECTPATH"


# Database username prompt
DBUSER=""
while true; do
  read -r -p "Enter your database username [root]: " input
  if [[ -z "$input" ]]; then
    DBUSER=root
    break
  else
    DBUSER=$input
    break
  fi
done

# Database password prompt
echo "Enter your database password: "
read -s DBPASS

# Database host prompt
echo "Note: If using Docker containers, use 127.0.0.1 instead of localhost."
DBHOST=""
while true; do
  read -r -p "Enter your database host [localhost]: " input
  if [[ -z "$input" ]]; then
    DBHOST=localhost
    break
  else
    DBHOST=$input
    break
  fi
done

# Database port prompt
DBPORT=""
while true; do
  read -r -p "Enter the database port [3306]: " input
  if [[ -z "$input" ]]; then
    DBPORT=3306
    break
  elif ! [[ "$input" =~ ^[0-9]+$ ]]; then
    echo "Invalid input. Please enter a number."
  else
    DBPORT=$input
    break
  fi
done

# Database name prompt
DBNAME=""
while true; do
  read -r -p "Enter the database name: " input
  if [[ -z "$input" ]]; then
    echo "Invalid input. Please enter a name."
  else
    DBNAME=$input
    break
  fi
done

# Site name prompt
SITENAME=""
while true; do
  read -r -p "Enter the site name: " input
  if [[ -z "$input" ]]; then
    echo "Invalid input. Please enter a site name."
  else
    SITENAME=$input
    break
  fi
done

# Site email prompt
EMAIL=""
while true; do
  read -r -p "Enter the site email: " input
  if [[ -z "$input" ]]; then
    echo "Invalid input. Please enter a site email."
  elif [[ ! "$input" =~ ^[a-zA-Z0-9._%+]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Invalid input. Please enter a valid email address."
  else
    EMAIL=$input
    break
  fi
done

# Profile installation name prompt
PROFILE=""
while true; do
  read -r -p "Enter the name of the profile that you want (developer, builder, communicator): " input
  if [[ -z "$input" ]]; then
    echo "Invalid input. Please enter a profile name."
  else
    PROFILE=$input
    break
  fi
done

start_process 

if [ -z "$LOCAL" ]; then LOCAL=true; fi

install_site
set_permissions "$LOCAL"
fix_permissions_issue

exit 0
