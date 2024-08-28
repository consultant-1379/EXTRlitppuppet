# only perform the operations in this script when installing
# $1 == "1" means its installation %post

if [ "$1" == "1" ]; then
    /sbin/service puppet restart
exit 0
