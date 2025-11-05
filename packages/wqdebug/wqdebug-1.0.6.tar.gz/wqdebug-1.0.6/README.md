# wqdebug

## Install
pip install wqdebug

## Usage
```cmd
# cmd or powershell or bash
wqdebug --help
```

### GDB
run gdb 
```cmd
# cmd or powershell or bash
wqdebug gdb
```

### LOG
log parse
```cmd
# cmd or powershell or bash
wqdebug log
```
origin log:
```
2025-05-28 14:38:45 325 [A-105 ] [285.6]>[D] [BT] app_bt_send_rpc_cmd 5 ret=0
2025-05-28 14:38:45 332 [B-85  ] [294.7]>[I] [LIB] bt handle cmd:1
2025-05-28 14:38:45 331 [A-116 ] [292.4]>[D] [MAIN] app_send_msg type:3 id:8001 param_len:4 priority:0
2025-05-28 14:38:50 633 [A-401 ] [6065.2]>[I] [WWS] app_wws_send_remote_msg type:16 id:5 param_len:12
2025-05-28 14:38:50 599 [A-387 ] [6035.1]>[I] [WWS] wws_handle_remote_msg type:16 id:5 param_len:12
2025-06-21 18:42:57 180 [A-230 ] [267150.6]>app_send_msg_delay type:2 id:2 delay:1000
2025-06-21 18:42:57 182 [A-231 ] [267150.8]>handle_msg type:2 id:2 run_time_ms:0
2025-06-21 18:42:57 225 [A-235 ] [267214.8]>app_cancel_delay_msg type:13 id:1 triggered:0
2025-05-28 14:39:10 249 [A-699 ] [25622.5]>[I] [BT] sys_state 0x8=>0x10
2025-05-28 14:38:47 901 [B-267 ] [3332.5]>[I] [BT_CTRL] TDS:lc_lmp_tx_cfm:idx=0,opcode=38,ext_opcode=0
2025-05-28 14:38:47 901 [B-268 ] [3332.9]>[I] [BT_CTRL] TDS:lc_lmp_rx:idx=0,opcode=39,ext_opcode=0
2025-05-28 14:38:47 902 [B-270 ] [3334.0]>[I] [BT_CTRL] TDS:lc_lmp_tx:idx=0,opcode=40,ext_opcode=0
2025-05-28 14:41:35 028 [A-256 ] [170432.1]>[W] [DRIVER] [auto][WARNING]vector:117 time 289
2025-06-21 18:42:58 194 [A-379 ] [268150.1]>WARNING: This rpc task is too heavy!""src:1, cmd:24, interval 30659
2025-06-21 18:21:53 847 [B-109 ] [1352.0]>RX HCI_COMMAND_COMPLETE_EVENT. Packets Num: 5, Opcode: 0xFC65, Status: 0x00
```
replace log:
```
2025-05-28 14:38:45 325 [A-105 ] [285.6]>[D] [BT] app_bt_send_rpc_cmd 5(BT_CMD_GET_LOCAL_ADDR) ret=0(BT_RESULT_SUCCESS)
2025-05-28 14:38:45 332 [B-85  ] [294.7]>[I] [LIB] bt handle cmd:1(BT_CMD_SET_ENABLED)
2025-05-28 14:38:45 331 [A-116 ] [292.4]>[D] [MAIN] app_send_msg type:3(MSG_TYPE_EVT) id:8001 param_len:4 priority:0
2025-05-28 14:38:50 633 [A-401 ] [6065.2]>[I] [WWS] app_wws_send_remote_msg type:16(MSG_TYPE_OTA) id:5 param_len:12
2025-05-28 14:38:50 599 [A-387 ] [6035.1]>[I] [WWS] wws_handle_remote_msg type:16(MSG_TYPE_OTA) id:5 param_len:12
2025-06-21 18:42:57 180 [A-230 ] [267150.6]>app_send_msg_delay type:2(MSG_TYPE_WWS) id:2 delay:1000
2025-06-21 18:42:57 182 [A-231 ] [267150.8]>handle_msg type:2(MSG_TYPE_WWS) id:2 run_time_ms:0
2025-06-21 18:42:57 225 [A-235 ] [267214.8]>app_cancel_delay_msg type:13(MSG_TYPE_USR_CFG) id:1 triggered:0
2025-05-28 14:39:10 249 [A-699 ] [25622.5]>[I] [BT] sys_state 0x8(STATE_CONNECTABLE)=>0x10(STATE_AG_PAIRING)
2025-05-28 14:38:47 901 [B-267 ] [3332.5]>[I] [BT_CTRL] TDS:lc_lmp_tx_cfm:idx=0,opcode=38(LMP_VER_RES_OPCODE),ext_opcode=0
2025-05-28 14:38:47 901 [B-268 ] [3332.9]>[I] [BT_CTRL] TDS:lc_lmp_rx:idx=0,opcode=39(LMP_FEATS_REQ_OPCODE),ext_opcode=0
2025-05-28 14:38:47 902 [B-270 ] [3334.0]>[I] [BT_CTRL] TDS:lc_lmp_tx:idx=0,opcode=40(LMP_FEATS_RES_OPCODE),ext_opcode=0
2025-05-28 14:41:35 028 [A-256 ] [170432.1]>[W] [DRIVER] [auto][WARNING]vector:117(WIC_WAKEN_UP_INT_BT2DCORE) time 289
2025-06-21 18:42:58 194 [A-379 ] [268150.1]>WARNING: This rpc task is too heavy!""src:1(BT_CORE), cmd:24(RPC_CMD_audio_sys_create_stream_ext), interval 30659
2025-06-21 18:21:53 847 [B-109 ] [1352.0]>RX HCI_COMMAND_COMPLETE_EVENT. Packets Num: 5, Opcode: 0xFC65, Status: 0x00
```

## Develop
pip install -e .

## Test
```cmd
pytest
```


