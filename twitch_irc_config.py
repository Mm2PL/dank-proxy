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
import inspect
import os
import queue
import sys
import uuid
import time
import typing
import traceback

import aiohttp
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
                    send_time=None, disable_auto_multiple=False):
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

    if '\n' in text and not disable_auto_multiple:
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
                input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                    _format_message(channel, text, 'TriHard', 'BOT', badges=['twitchbot/1'], user_type='mod')
                )
            elif text.startswith('/test ') or text == '/test':
                data = b''
                input_queues[conn_id + ENABLE_DOUBLE_CONNECTION].put(
                    _format_message(channel, text='TriHard', user_from='bot', display_name='TriHard',
                                    badges=['1979-revolution_1/1',
                                            '60-seconds_1/1',
                                            '60-seconds_2/1',
                                            '60-seconds_3/1',
                                            'H1Z1_1/1',
                                            'admin/1',
                                            'anomaly-2_1/1',
                                            'anomaly-warzone-earth_1/1',
                                            'anonymous-cheerer/1',
                                            'axiom-verge_1/1',
                                            'battlechefbrigade_1/1',
                                            'battlechefbrigade_2/1',
                                            'battlechefbrigade_3/1',
                                            'battlerite_1/1',
                                            'bits/1',
                                            'bits/100',
                                            'bits/1000',
                                            'bits/10000',
                                            'bits/100000',
                                            'bits/1000000',
                                            'bits/1250000',
                                            'bits/1500000',
                                            'bits/1750000',
                                            'bits/200000',
                                            'bits/2000000',
                                            'bits/25000',
                                            'bits/2500000',
                                            'bits/300000',
                                            'bits/3000000',
                                            'bits/3500000',
                                            'bits/400000',
                                            'bits/4000000',
                                            'bits/4500000',
                                            'bits/5000',
                                            'bits/50000',
                                            'bits/500000',
                                            'bits/5000000',
                                            'bits/600000',
                                            'bits/700000',
                                            'bits/75000',
                                            'bits/800000',
                                            'bits/900000',
                                            'bits-charity/1',
                                            'bits-leader/1',
                                            'bits-leader/2',
                                            'bits-leader/3',
                                            'brawlhalla_1/1',
                                            'broadcaster/1',
                                            'broken-age_1/1',
                                            'bubsy-the-woolies_1/1',
                                            'clip-champ/1',
                                            'cuphead_1/1',
                                            'darkest-dungeon_1/1',
                                            'deceit_1/1',
                                            'devil-may-cry-hd_1/1',
                                            'devil-may-cry-hd_2/1',
                                            'devil-may-cry-hd_3/1',
                                            'devil-may-cry-hd_4/1',
                                            'devilian_1/1',
                                            'duelyst_1/1',
                                            'duelyst_2/1',
                                            'duelyst_3/1',
                                            'duelyst_4/1',
                                            'duelyst_5/1',
                                            'duelyst_6/1',
                                            'duelyst_7/1',
                                            'enter-the-gungeon_1/1',
                                            'eso_1/1',
                                            'extension/1',
                                            'firewatch_1/1',
                                            'founder/0',
                                            'frozen-cortext_1/1',
                                            'frozen-synapse_1/1',
                                            'getting-over-it_1/1',
                                            'getting-over-it_2/1',
                                            'glhf-pledge/1',
                                            'global_mod/1',
                                            'heavy-bullets_1/1',
                                            'hello_neighbor_1/1',
                                            'hype-train/1',
                                            'hype-train/2',
                                            'innerspace_1/1',
                                            'innerspace_2/1',
                                            'jackbox-party-pack_1/1',
                                            'kingdom-new-lands_1/1',
                                            'moderator/1',
                                            'okhlos_1/1',
                                            'overwatch-league-insider_1/1',
                                            'overwatch-league-insider_2018B/1',
                                            'overwatch-league-insider_2019A/1',
                                            'overwatch-league-insider_2019A/2',
                                            'overwatch-league-insider_2019B/1',
                                            'overwatch-league-insider_2019B/2',
                                            'overwatch-league-insider_2019B/3',
                                            'overwatch-league-insider_2019B/4',
                                            'overwatch-league-insider_2019B/5',
                                            'partner/1',
                                            'power-rangers/0',
                                            'power-rangers/1',
                                            'power-rangers/2',
                                            'power-rangers/3',
                                            'power-rangers/4',
                                            'power-rangers/5',
                                            'power-rangers/6',
                                            'premium/1',
                                            'psychonauts_1/1',
                                            'raiden-v-directors-cut_1/1',
                                            'rift_1/1',
                                            'samusoffer_beta/0',
                                            'staff/1',
                                            'starbound_1/1',
                                            'strafe_1/1',
                                            'sub-gift-leader/1',
                                            'sub-gift-leader/2',
                                            'sub-gift-leader/3',
                                            'sub-gifter/1',
                                            'sub-gifter/10',
                                            'sub-gifter/100',
                                            'sub-gifter/1000',
                                            'sub-gifter/25',
                                            'sub-gifter/250',
                                            'sub-gifter/5',
                                            'sub-gifter/50',
                                            'sub-gifter/500',
                                            'subscriber/0',
                                            'subscriber/1',
                                            'superhot_1/1',
                                            'the-surge_1/1',
                                            'the-surge_2/1',
                                            'the-surge_3/1',
                                            'this-war-of-mine_1/1',
                                            'titan-souls_1/1',
                                            'treasure-adventure-world_1/1',
                                            'turbo/1',
                                            'twitchbot/1',
                                            'twitchcon2017/1',
                                            'twitchcon2018/1',
                                            'twitchconAmsterdam2020/1',
                                            'twitchconEU2019/1',
                                            'twitchconNA2019/1',
                                            'twitchconNA2020/1',
                                            'tyranny_1/1',
                                            'vga-champ-2017/1',
                                            'vip/1',
                                            'warcraft/alliance',
                                            'warcraft/horde'],
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
                    # always prefer the longest match.
                    if inspect.iscoroutinefunction(commands[longest]):
                        o = await (commands[longest](text, channel))
                    else:
                        o = commands[longest](text, channel)
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


def _localcommands(text, channel):
    return f'Local commands: {", ".join(i for i in commands)}'


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


commands['/py'] = _eval_command


async def _command_recent_messages(text, channel):
    async with aiohttp.request('get', f'https://recent-messages.robotty.de/api/v2/recent-messages/{channel}'
                                      f'?clearchatToNotice=true') as request:
        data = await request.json()
        try:
            return (
                    _format_message(channel, '\x01ACTION ---------------------------------------', color='#AAAAAA')
                    + _format_message(channel, '\x01ACTION Loaded recent messages!', color='#AAAAAA')
                    + _format_message(channel, '\x01ACTION ---------------------------------------', color='#AAAAAA')
                    + ('\r\n'.join(data['messages'])).encode('utf-8') + b'\r\n'
            )
        except:
            return 'Unable to fetch recent messages.'


commands['/recent'] = _command_recent_messages


async def _test_command(text, channel):
    return _format_message(channel, text.replace('/test123', '', 1).replace('\\n', '\n'),
                           disable_auto_multiple=True)

commands['/test123'] = _test_command

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(generic.main())
