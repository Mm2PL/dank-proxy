#  This is a proxy that can replace data going thought it.
#  Copyright (C) 2019 Mm2PL
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import builtins
import importlib.util
import os
import queue
import sys
import uuid
import time
import typing
import traceback

import regex
import twitchirc

sys.argv += [
    '-b', 'irc.chat.twitch.tv', '-P', '6697', '-p', '42072', '--ssl'
]
import generic

input_queues: typing.Dict[int, queue.Queue] = {}
ENABLE_DOUBLE_CONNECTION = True
ENABLE_SELF_HIGHLIGHT = False


def _format_message(channel, text, user_from='ProxyBot', display_name=None, badges=None, color='#FF69B4', emotes=None,
                    message_uuid=None, mod=False, room_id=1, sub=False, turbo=False, user_id=0, user_type='',
                    send_time=None):
    if display_name is None:
        display_name = user_from
    if badges is None:
        badges = ['twitchbot/1']
    if emotes is None:
        emotes = []
    if message_uuid is None:
        message_uuid = uuid.uuid4()
    if send_time is None:
        send_time = round(time.time())

    if '\n' in text:
        output = b''
        for line in text.split('\n'):
            output += _format_message(channel, line, user_from, display_name, badges, color, emotes, message_uuid, mod,
                                      room_id, sub, turbo, user_id, user_type, send_time)
        return output
    return (f'@badge-info=;badges={",".join(badges)};'
            f'color={color};display-name={display_name};emotes={"/".join(emotes)};'
            f'flags=;id={message_uuid};mod={int(mod)};room-id={room_id};'
            f'subscriber={int(sub)};tmi-sent-ts={send_time};'
            f'turbo={int(turbo)};user-id={user_id};user-type={user_type} '
            f':{user_from}!{user_from}@{user_from}.tmi.twitch.tv '
            f'PRIVMSG #{channel} '
            f':{text}\r\n').encode('utf-8')


commands = {}
current_eval_locals = {}


class OutputProcessor(generic.Replacement):
    def __init__(self):
        super().__init__('', None)
        self.regex = regex.compile(r'PRIVMSG #(.*?) :(.*?)$')

    async def sub(self, data: bytes, conn_id) -> bytes:
        _maybe_init_queue(conn_id)
        _maybe_init_queue(conn_id + ENABLE_DOUBLE_CONNECTION)
        d = data.decode('utf-8').replace('\r\n', '\n')
        result = self.regex.match(d)
        if result:  # commands
            channel = result.group(1)
            text = result.group(2)
            if text.startswith('/$'):
                text = text.replace('/$', '/w supibot $')
                data = f'PRIVMSG {channel} :{text}\r\n'.encode('utf-8')
                # input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                #     (
                #         f'@badge-info=;badges=twitchbot/1;'
                #         f'color=#FF69B4;display-name=BOT;emotes=;'
                #         f'flags=;id={uuid.uuid4()!s};mod=1;room-id=1;'
                #         f'subscriber=1;tmi-sent-ts={round(time.time())};'
                #         f'turbo=0;user-id=31400525;user-type= '
                #         f':TriHard!TriHard@TriHard.tmi.twitch.tv '
                #         f'PRIVMSG #{channel} '
                #         f':{text}\r\n'
                #     ).encode('utf-8'))
                input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                    _format_message(channel, text, 'TriHard', 'BOT', badges=['twitchbot/1'], user_type='mod')
                )
            elif text.startswith('/test'):
                data = b''
                input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                    _format_message(channel, text='TriHard', user_from='bot', display_name='TriHard',
                                    badges=[
                                        'staff/1',
                                        'anonymous-cheerer/1',
                                        'bits/5000000',
                                        'global_mod/1',
                                        'sub-gift-leader/1',
                                        'sub-gifter/1000',
                                        'twitchbot/1'
                                    ],
                                    emotes=['120232:0-6'],
                                    mod=True, sub=True, turbo=True, user_type='mod', send_time=0
                                    )
                )
            else:
                matches = []
                for c in commands:
                    if text.startswith(c):
                        matches.append(c)
                if matches:
                    longest = max([(i, len(i)) for i in matches], key=lambda x: x[1])[0]
                    o = commands[longest](text, channel)  # always prefer the longest match.
                    if isinstance(o, str):
                        input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                            _format_message(channel, o)
                        )
                    elif isinstance(o, bytes):
                        input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(o)
                    elif isinstance(o, list):
                        if len(o) == 0:
                            return b''
                        if isinstance(o[0], str):
                            for i in o:
                                input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                                    _format_message(channel, i)
                                )
                        elif isinstance(o[0], bytes):
                            for i in o:
                                input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(i)
                    return b''
        return data


def _maybe_init_queue(conn_id):
    if conn_id not in input_queues:
        input_queues[conn_id] = queue.Queue()


# b'@badge-info=subscriber/2;badges=vip/1,subscriber/0,'
# b'glhf-pledge/1;color=#DAA520;display-name=Mm2PL;emote-only=1;emotes=300436895:0-9;flags=;id=fd5309e1-07bd-4c9b
# -b5ff'
# b'-aee04a746d27;mod=0;room-id=31400525;subscriber=1;tmi-sent-ts=1577316708781;turbo=0;user-id=117691339;user
# -type='
# b':mm2pl!mm2pl@mm2pl.tmi.twitch.tv PRIVMSG #supinic :supiniOkay\r\n'
last_user_state = {

}


class InputProcessor(generic.Replacement):
    def __init__(self):
        super().__init__('', None)
        self.regex = None
        self.user_state_regex = regex.compile(r'@badge-info=(?P<badgeinfo>.*);'
                                              r'badges=(?P<badges>.*?);'
                                              r'color=(?P<color>(?:#[0-9A-F]{6})|);'
                                              r'display-name='
                                              r'(?P<displayname>(?:[a-zA-Z0-9]|\p{Han}|\p{Hiragana}|\p{'
                                              r'Katakana})+);'
                                              r'emote-sets=(?P<emotesets>[0-9,]+)+;'
                                              r'mod=(?P<mod>[10]);'
                                              r'subscriber=(?P<sub>[10]);'
                                              r'user-type=(?P<usertype>mod|) '
                                              r':tmi\.twitch\.tv USERSTATE (?P<channel>#[a-z0-9_-]+)$')
        self.privmsg_pattern = regex.compile(twitchirc.PRIVMSG_PATTERN_TWITCH)

    def sub(self, data: bytes, conn_id) -> bytes:
        global last_user_state
        _maybe_init_queue(conn_id)
        d = data.decode('utf-8').replace('\r\n', '\n')
        print(d)
        user_state = self.user_state_regex.match(d)
        if ENABLE_SELF_HIGHLIGHT and user_state:
            print('USERSTATE!!!', repr(user_state.group('channel').lstrip(' #')))
            print('USERSTATE!!!', repr(user_state.group('channel').lstrip(' #')))
            print('USERSTATE!!!', repr(user_state.group('channel').lstrip(' #')))
            last_user_state[user_state.group('channel').lstrip(' #')] = user_state
            d = regex.sub('color=((?:#[0-9A-F]{6})|)', 'color=#FF0000', d)
            data = d.replace('\n', '\r\n').encode('utf-8')
        privmsg_match = self.privmsg_pattern.match(d)
        if privmsg_match and privmsg_match.group(3) in last_user_state:
            user = twitchirc.process_twitch_flags(privmsg_match.group(1))
            if user['display-name'] == last_user_state[privmsg_match.group(3)].group('displayname'):
                if ENABLE_SELF_HIGHLIGHT:
                    d = regex.sub('color=((?:#[0-9A-F]{6})|)', 'color=#FF0000', d)
                data = d.replace('\n', '\r\n').encode('utf-8')

        elif privmsg_match and privmsg_match.group(3) not in last_user_state:
            print('not xd', repr(privmsg_match.group(3)))

        while not input_queues[conn_id].empty():
            print('not empty', conn_id)
            d = input_queues[conn_id].get()
            print(d)
            input_queues[conn_id].task_done()
            data = data + d
            print(data)
        else:
            print('empty', conn_id)
        return data


generic.regexs['out'].append(OutputProcessor())
generic.regexs['in'].append(InputProcessor())


def _localcommands(text):
    return f'Local commands: /py, {", ".join(i for i in commands)}'


commands['/localcommands'] = _localcommands


async def _eval_command(text, channel):
    if not text.startswith('/py '):
        return _format_message(channel, 'Usage: /py (expression)', color='#AA0000')
        # input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
        #     _format_message(channel, 'Usage: /py (expression)', color='#AA0000')
        # )

    else:
        t: typing.List[str] = text.split(' ', 1)
        output = [_format_message(channel, f'>>> {t[1]}', color='#00FF00')]

        # input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
        #     _format_message(channel, f'>>> {t[1]}', color='#00FF00')
        # )

        def _import_load(module, as_=None):
            if as_ is None:
                as_ = module
            current_eval_locals[as_] = __import__(module)
            return current_eval_locals[as_]

        def _import_file_load(path, as_=None):
            if as_ is None:
                as_ = os.path.splitext(os.path.split(path)[1])[0]
            print(f' -> Name: {as_}')
            # noinspection PyProtectedMember
            spec: importlib._bootstrap.ModuleSpec = importlib.util.spec_from_file_location(as_,
                                                                                           path)

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            current_eval_locals[as_] = module
            return module

        def _e(name, value):
            current_eval_locals[name] = value

        gs = {name: getattr(builtins, name) for name in dir(builtins)}
        gs.update({
            'input_queues': input_queues,
            'ENABLE_DOUBLE_CONNECTION': ENABLE_DOUBLE_CONNECTION,
            '_format_message': _format_message,
            'sys': sys,
            'os': os,
            'i_': _import_load,
            'i_f_': _import_file_load,
            '_e': _e
        })

        # noinspection PyBroadException
        try:
            ret_val = eval(compile(t[1], channel, 'eval'), gs, current_eval_locals)
        except BaseException:
            exc = traceback.format_exc(100).split('\n')
            for line in exc:
                line = line.replace('\n', '')
                print(line)
                # input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                #     _format_message(channel, f'E: {line}', color='#FF0000')
                # )
                output.append(_format_message(channel, f'E: {line}', color='#FF0000'))
        else:
            # input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
            #     _format_message(channel, f'__O: {ret_val}', color='#00FF00')
            # )
            output.append(_format_message(channel, f'__O: {ret_val}', color='#00FF00'))
            current_eval_locals['_'] = ret_val
    return output


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(generic.main())
