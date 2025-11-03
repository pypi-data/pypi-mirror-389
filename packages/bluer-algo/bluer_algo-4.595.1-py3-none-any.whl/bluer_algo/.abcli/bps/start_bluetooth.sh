#! /usr/bin/env bash

function bluer_algo_bps_start_bluetooth() {
    local options=$1
    local verbose=$(bluer_ai_option_int "$options" verbose 0)

    bluer_ai_log "starting bluetooth..."

    bluer_ai_eval - \
        sudo systemctl start bluetooth
    [[ $? -ne 0 ]] && return 1

    [[ "$verbose" == 1 ]] &&
        bluer_ai_eval - \
            sudo systemctl status \
            --no-pager bluetooth

    bluer_ai_eval - \
        sudo bluetoothctl power on
    [[ $? -ne 0 ]] && return 1

    bluer_ai_eval - \
        sudo bluetoothctl discoverable on
    [[ $? -ne 0 ]] && return 1

    [[ "$verbose" == 1 ]] &&
        bluer_ai_eval - \
            sudo bluetoothctl show

    return 0
}
