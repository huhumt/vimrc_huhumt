#!/usr/bin/env bash

# echo PASSWORD | openssl aes-256-cbc -e -a -iter +4096
google_test_auth_aes256="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
github_test_auth_aes256="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

lower_domain=$(echo "$1" | tr '[:upper:]' '[:lower:]')
if [ "$lower_domain" = "google" ]; then
    target_aes256=$google_test_auth_aes256
    target_name="Google 2FA code: "
else
    target_aes256=$github_test_auth_aes256
    target_name="Github 2FA code: "
fi

target_secret=$(echo "$target_aes256" | openssl aes-256-cbc -d -a -iter +4096)
echo "$target_name $(oathtool -b --totp "$target_secret")"
