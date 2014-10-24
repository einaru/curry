#!/usr/bin/bash
#
# bump-version.sh
#
# Command-line utilty script to bump the version of a software project.
# Accepts only numeric version numbers.

show_help() {
	cat <<-EndShowHelp
	usage: $0 [-h] [version]

	Bump a version number.

	positional arguments:

	  version    the new version number, if no arguments is provided, the
	             current version number is shown.

	optional arguments:

	  -h, --help show this help message and exit
	EndShowHelp
}

error() {
	echo -e "$0: error: $1" >&2
}

die() {
	error "$1"
	exit 1
}

# Version checking algorithm
#
# Returns 9 if the first value is less than the second.
# Returns 10 if they are equal.
# Returns 11 if the first value is greater than the second.
#
# See: http://lists.us.dell.com/pipermail/dkms-devel/2004-July/000142.html
do_version_check() {
	[[ "$1" == "$2" ]] && return 10

	v1_front=$(echo $1 | cut -d "." -f -1)
	v1_back=$(echo $1 | cut -d "." -f 2-)
	v2_front=$(echo $2 | cut -d "." -f -1)
	v2_back=$(echo $2 | cut -d "." -f 2-)

	if [[ "$v1_front" != "$1" ]] || [[ "$v2_front" != "$2" ]]; then
		[[ "$v1_front" -gt "$v2_front" ]] && return 11
		[[ "$v1_front" -lt "$v2_front" ]] && return 9

		[[ "$v1_front" == "$1" ]] || [[ -z "$v1_back" ]] && v1_back=0
		[[ "$v2_front" == "$2" ]] || [[ -z "$v2_back" ]] && v2_back=0
		do_version_check "$v1_back" "$v2_back"
		return $?
	else
		[[ "$1" -gt "$2" ]] && return 11 || return 9
	fi
}

bump_version() {
	local old new
	old=$1
	new=$2

	sed -i "s/version = '$old'/version = '$new'/g" $VERSION_FILE
	sed -i "s/pkgver='$old'/pkgver='$new'/g" $PKGBUILD_FILE
}

# Setup some initial variables
GITROOT=$(git rev-parse --show-toplevel)
cd $GITROOT

VERSION_FILE="./curry/__init__.py"
PKGBUILD_FILE="./arch/PKGBUILD"
OLD_VERSION=$(cat $VERSION_FILE | grep 'version' | sed 's/[^0-9.]//g')

# Check for optional arguments
case "$1" in
	-h|--help) show_help ; exit 0 ;;
esac

NEW_VERSION="$1"
if [[ -z $NEW_VERSION ]]; then
	echo "$OLD_VERSION"
	exit 0
fi

# DONE:2014-10-19:einar: validate version number
[[ $NEW_VERSION =~ ^-?[0-9.]+$ ]] || die "illegal version number: $NEW_VERSION"

do_version_check $OLD_VERSION $NEW_VERSION
result=$?

case "$result" in
	(10) echo "Nothing to do! ($NEW_VERSION == $OLD_VERSION)" >&2 ;;
	(11) echo "Bailing! ($NEW_VERSION < $OLD_VERSION)" >&2 ;;
	(9)
		bump_version $OLD_VERSION $NEW_VERSION
		echo "New version is '$NEW_VERSION'"
		git add $VERSION_FILE $PKGBUILD_FILE
		echo "Now run: git commit -m 'Bumped version to v$NEW_VERSION'"
		result=0
esac

exit $result
