#!/bin/bash
set -e
for dir in raphson_mp/translations/*;
do
    echo "compiling messages: $dir"
    msgfmt $dir/LC_MESSAGES/messages.po -o $dir/LC_MESSAGES/messages.mo
done
