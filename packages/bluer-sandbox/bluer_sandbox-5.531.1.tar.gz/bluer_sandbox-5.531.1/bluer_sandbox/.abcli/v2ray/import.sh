#! /usr/bin/env bash

function bluer_sandbox_v2ray_import() {
    local options=$1
    local do_cat=$(bluer_ai_option_int "$options" cat 0)

    local vless=$2
    if [[ -z "$vless" ]]; then
        bluer_ai_log_error "vless not found."
        return 1
    fi

    local object_name=v2ray-import-$(bluer_ai_string_timestamp)
    local object_path=$ABCLI_OBJECT_ROOT/$object_name
    local filename=$object_path/config.json
    bluer_ai_log "importing to $filename..."

    mkdir -pv $object_path

    local repo_path=$abcli_path_git/v2ray-uri2json
    if [[ ! -d "$repo_path" ]]; then
        bluer_ai_git_clone \
            https://github.com/ImanSeyed/v2ray-uri2json.git
        [[ $? -ne 0 ]] && return 1
    fi

    cd $abcli_path_git/v2ray-uri2json
    [[ $? -ne 0 ]] && return 1

    [[ -f "./config.json" ]] &&
        rm -v ./config.json

    bash \
        scripts/vless2json.sh \
        "$vless"
    [[ $? -ne 0 ]] && return 1

    mv -v ./config.json \
        $ABCLI_OBJECT_ROOT/$object_name/config.json
    [[ $? -ne 0 ]] && return 1

    python3 -m bluer_sandbox.v2ray \
        complete_import \
        --object_name $object_name
    [[ $? -ne 0 ]] && return 1

    sudo mkdir -pv /usr/local/etc/v2ray
    sudo cp -v \
        $filename \
        /usr/local/etc/v2ray/config.json

    [[ "$do_cat" == 1 ]] &&
        bluer_ai_cat $filename

    return 0
}
