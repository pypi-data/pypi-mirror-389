#! /usr/bin/env bash

function bluer_sandbox_v2ray_install() {
    local options=$1
    local do_import=$(bluer_ai_option_int "$import_options" import 0)

    if [[ "$abcli_is_mac" == false ]]; then
        bluer_ai_log_error "@tray start only works on mac."
        return 1
    fi

    local thing
    for thing in v2ray jq; do
        bluer_ai_eval \
            ,$options \
            brew install $thing
        [[ $? -ne 0 ]] && return 1
    done

    if [[ "$do_import" == 1 ]]; then
        bluer_sandbox_v2ray_import "$@"
        [[ $? -ne 0 ]] && return 1
    fi
}
