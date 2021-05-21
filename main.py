import copy
import re, json, time, ctypes, hashlib
import win32api,win32gui,win32con
from pywinauto import clipboard
import command_release

with open('conf.json', encoding="utf8") as f:
    config = json.load(f)

chat_pattern = '\[.*\] \[.*\] (?P<CHAT>.*)'
command_pattern = '@bot ?- ?(?P<MAIN_CMD>.+)\((?P<SUB_CMD>.*)\) ?(?P<DECO>.*)'
save_chat_list = []
save_hash_list = []

def open_chat_room(chat_room, kakao_talk):
    hwndkakao = win32gui.FindWindow(None, kakao_talk)
    hwndkakao_edit1 = win32gui.FindWindowEx( hwndkakao, None, "EVA_ChildWindow", None)
    hwndkakao_edit2_1 = win32gui.FindWindowEx( hwndkakao_edit1, None, "EVA_Window", None)
    hwndkakao_edit2_2 = win32gui.FindWindowEx( hwndkakao_edit1, hwndkakao_edit2_1, "EVA_Window", None)
    hwndkakao_edit3 = win32gui.FindWindowEx( hwndkakao_edit2_2, None, "Edit", None)

    win32api.SendMessage(hwndkakao_edit3, win32con.WM_SETTEXT, 0, chat_room)
    time.sleep(1) 
    push_enter(hwndkakao_edit3)
    time.sleep(1)

def copy_chat_from_room(chat_room):
    hwndMain = win32gui.FindWindow( None, chat_room)
    hwndListControl = win32gui.FindWindowEx(hwndMain, None, "EVA_VH_ListControl_Dblclk", None)
    combe_hot_key(hwndListControl, ord('A'), [win32con.VK_CONTROL], False)
    time.sleep(1)
    combe_hot_key(hwndListControl, ord('C'), [win32con.VK_CONTROL], False)
    ctext = clipboard.GetData()
    return ctext.split('\r\n')

def combe_hot_key(hwnd, key, shift, specialkey):
    if win32gui.IsWindow(hwnd):

        ThreadId = ctypes.WinDLL("user32").GetWindowThreadProcessId(hwnd, None)

        lparam = win32api.MAKELONG(0, ctypes.WinDLL("user32").MapVirtualKeyA(key, 0))
        msg_down = win32con.WM_KEYDOWN
        msg_up = win32con.WM_KEYUP

        if specialkey:
            lparam = lparam | 0x1000000

        if len(shift) > 0:
            pKeyBuffers = (ctypes.c_ubyte * 256)()
            pKeyBuffers_old = (ctypes.c_ubyte * 256)()

            win32gui.SendMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
            ctypes.WinDLL("user32").AttachThreadInput(win32api.GetCurrentThreadId(), ThreadId, True)
            ctypes.WinDLL("user32").GetKeyboardState(ctypes.byref(pKeyBuffers_old))

            for modkey in shift:
                if modkey == win32con.VK_MENU:
                    lparam = lparam | 0x20000000
                    msg_down = win32con.WM_SYSKEYDOWN
                    msg_up = win32con.WM_SYSKEYUP
                pKeyBuffers[modkey] |= 128

            ctypes.WinDLL("user32").SetKeyboardState(ctypes.byref(pKeyBuffers))
            time.sleep(0.01)
            win32api.PostMessage(hwnd, msg_down, key, lparam)
            time.sleep(0.01)
            win32api.PostMessage(hwnd, msg_up, key, lparam | 0xC0000000)
            time.sleep(0.01)
            ctypes.WinDLL("user32").SetKeyboardState(ctypes.byref(pKeyBuffers_old))
            time.sleep(0.01)
            ctypes.WinDLL("user32").AttachThreadInput(win32api.GetCurrentThreadId(), ThreadId, False)

        else:
            win32gui.SendMessage(hwnd, msg_down, key, lparam)
            win32gui.SendMessage(hwnd, msg_up, key, lparam | 0xC0000000)

def push_enter(hwnd):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    time.sleep(0.01)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)

def setting_before_start(chat_room, kakao_talk, chat_count):
    open_chat_room(chat_room, kakao_talk)
    chat_list = copy_chat_from_room(chat_room)
    chat_list.pop()
    for x in range(0, chat_count):
        save_chat_list.append(chat_list.pop())
    for x in save_chat_list:
        sample_hash = hashlib.sha256(x.encode('UTF-8')).hexdigest()
        save_hash_list.append(sample_hash)
    return save_chat_list, save_hash_list

def kakao_sendtext(chat_name, text):
    hwndMain = win32gui.FindWindow( None, chat_name)
    hwndEdit = win32gui.FindWindowEx( hwndMain, None, "RichEdit50W", None)

    win32api.SendMessage(hwndEdit, win32con.WM_SETTEXT, 0, text)
    push_enter(hwndEdit)

def chat_listener(chat_room, kakao_talk, delay, chat_count):
    global save_chat_list

    chat_filter = re.compile(chat_pattern)
    command_filter = re.compile(command_pattern)
    while True:
        new_chat_list = []
        open_chat_room(chat_room, kakao_talk)
        chat_list = copy_chat_from_room(chat_room)
        chat_list.pop()
        chat_list.reverse()
        for idx, chat in enumerate(chat_list):
            if chat_list[idx:idx+chat_count] == save_chat_list:
                tmp_list = copy.deepcopy(save_chat_list)
                save_chat_list = copy.deepcopy(new_chat_list)
                if len(new_chat_list) < chat_count:
                    for x in range(0, chat_count - len(new_chat_list)):
                        save_chat_list.append(tmp_list[x])
                elif len(new_chat_list) > chat_count:
                    save_chat_list = new_chat_list[0:chat_count]
                print("new: " + str(new_chat_list))
                for new_chat in new_chat_list:
                    real_chat = chat_filter.search(new_chat).groupdict()['CHAT']
                    cmd_chat = command_filter.search(real_chat)
                    if cmd_chat:
                        print("cmd_chat: " + str(cmd_chat.groupdict()))
                        cmd_lib = cmd_chat.groupdict()
                        res_cmd = command_release.command_body(cmd_lib['MAIN_CMD'], cmd_lib['SUB_CMD'], cmd_lib['DECO'])
                        print("response: " + str(res_cmd))
                        kakao_sendtext(chat_room, res_cmd)
                break
            else:
                new_chat_list.append(chat)
                
        time.sleep(delay)

def run_chat_bot(*spec):
    bot_spec = spec[0]
    kakao_talk_name = bot_spec['KAKAO_TALK_NAME']
    chat_room_title = bot_spec['KAKAO_TALK_CHAT_ROOM_TITLE']
    delay_time = bot_spec['MONITORING_DELAY']
    save_lastest_chat_count = bot_spec['SAVE_LASTEST_CHAT_COUNT']

    setting_before_start(chat_room_title, kakao_talk_name, save_lastest_chat_count)
    chat_listener(chat_room_title, kakao_talk_name, delay_time, save_lastest_chat_count)

if __name__ == '__main__':
    run_chat_bot(config)

