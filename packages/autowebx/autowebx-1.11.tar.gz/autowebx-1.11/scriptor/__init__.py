import re
from dataclasses import dataclass
from json import loads
from pathlib import Path
from typing import Any, Iterator, Sequence
from urllib.parse import urlparse, parse_qs
from xml.etree.ElementTree import ElementTree, Element

from scriptor.utils import classify_url_params, to_snake_case, is_json, generate_generic_pattern


class Request:
    def __init__(self, index: int, element: Element):
        self.index = index
        self.url = element.find('url').text
        self.method = element.find('method').text
        self.request = element.find('request').text
        self.response = element.find('response').text

    def __repr__(self):
        return self.url


class PayloadDict(dict):
    def __init__(self, content: dict | str | None = None):
        super().__init__()
        if not content:
            return
        if type(content) == str:
            if is_json(content):
                self.type = str
                for k, v in loads(content).items():
                    if isinstance(v, dict) or (type(v) == str and is_json(v) and not v.isnumeric()):
                        self[k] = PayloadDict(v)
            else:
                raise ValueError('Not valid dict or JSON')
        elif isinstance(content, dict):
            self.type = dict
            for k, v in content.items():
                if isinstance(v, dict) or (type(v) == str and is_json(v) and not v.isnumeric()):
                    self[k] = PayloadDict(v)
                else:
                    self[k] = v
        else:
            raise ValueError('Not valid dict or JSON')


@dataclass
class PayloadEntry:
    kind: str
    value: Any
    dumps: int = 0
    is_expression: bool = False
    original: Any | None = None

    def requires_json(self) -> bool:
        if self.dumps > 0:
            return True
        if self.kind == 'dict':
            return any(entry.requires_json() for entry in self.value.values())
        if self.kind == 'list':
            return any(entry.requires_json() for entry in self.value)
        return False

    def iter_leaf_entries(self, path: tuple[Any, ...]) -> Iterator[tuple[tuple[Any, ...], 'PayloadEntry']]:
        if self.kind == 'dict':
            for key, entry in self.value.items():
                yield from entry.iter_leaf_entries(path + (key,))
        elif self.kind == 'list':
            for index, entry in enumerate(self.value):
                yield from entry.iter_leaf_entries(path + (index,))
        else:
            yield path, self

    def get_child(self, key: Any) -> 'PayloadEntry':
        if self.kind == 'dict':
            return self.value[key]
        if self.kind == 'list':
            return self.value[key]
        raise KeyError(key)

    def set_child(self, key: Any, entry: 'PayloadEntry') -> None:
        if self.kind == 'dict':
            self.value[key] = entry
            return
        if self.kind == 'list':
            self.value[key] = entry
            return
        raise KeyError(key)


class Function:
    def __init__(self, request: Request):
        self.request = request
        self.url: str = f'"{request.url}"'

        self.headers = dict()
        headers_lines = request.request.split('\n\n')[0].split('\n')[1:]
        for line in headers_lines:
            k, v = line.split(': ', 1)
            if k == 'Cookie':
                continue
            self.headers[k] = f"""'{v}'"""

        self.payload: dict[str, PayloadEntry] = dict()
        self.payload_type = ''
        raw_payload = request.request.split('\n\n')[-1]
        if raw_payload:
            if is_json(raw_payload):
                self.payload_type = 'json'
                decoded = loads(raw_payload)
            else:
                self.payload_type = 'data'
                decoded = {k: v[0] for k, v in parse_qs(raw_payload).items()}
            self.payload: dict[str, PayloadEntry] = {k: self._normalize_payload(v) for k, v in decoded.items()}

        self.requires_json = any(entry.requires_json() for entry in self.payload.values())
        self.results = list()
        self.name = f'{to_snake_case(self.url.split('/')[-2])}_{self.request.index}'

    def __repr__(self):
        return self.url

    def _normalize_payload(self, value: Any) -> PayloadEntry:
        if isinstance(value, dict):
            return PayloadEntry(
                kind='dict',
                value={k: self._normalize_payload(v) for k, v in value.items()},
            )
        if isinstance(value, list):
            return PayloadEntry(
                kind='list',
                value=[self._normalize_payload(item) for item in value],
            )
        if isinstance(value, str) and is_json(value) and not value.isnumeric():
            inner = self._normalize_payload(loads(value))
            inner.dumps += 1
            return inner
        original = value if isinstance(value, str) else str(value)
        return PayloadEntry(kind='value', value=value, original=original)

    def iter_payload_leaves(self) -> Iterator[tuple[tuple[Any, ...], PayloadEntry]]:
        for key, entry in self.payload.items():
            yield from entry.iter_leaf_entries((key,))

    def get_payload_entry(self, path: Sequence[Any]) -> PayloadEntry:
        if not path:
            raise ValueError('Empty payload path')
        entry = self.payload[path[0]]
        for key in path[1:]:
            entry = entry.get_child(key)
        return entry

    def set_payload_expression(self, path: Sequence[Any], expression: str) -> None:
        entry = self.get_payload_entry(path)
        entry.kind = 'value'
        entry.value = expression
        entry.is_expression = True
        entry.original = None
        self.requires_json = any(e.requires_json() for e in self.payload.values())



    def _render_entry(self, entry: PayloadEntry, indent_level: int) -> str:
        if entry.kind == 'dict':
            rendered = self._render_payload_dict(entry.value, indent_level)
        elif entry.kind == 'list':
            rendered = self._render_payload_list(entry.value, indent_level)
        else:
            rendered = str(entry.value) if entry.is_expression else repr(entry.value)
        for _ in range(entry.dumps):
            rendered = f'json.dumps({rendered})'
        return rendered

    def _render_payload_dict(self, payload: dict[str, PayloadEntry], indent_level: int) -> str:
        indent = ' ' * (indent_level * 4)
        inner_indent = ' ' * ((indent_level + 1) * 4)
        lines = ['{']
        for key, entry in payload.items():
            rendered = self._render_entry(entry, indent_level + 1)
            if '\n' in rendered:
                rendered = rendered.replace('\n', '\n' + inner_indent)
            lines.append(f"{inner_indent}'{key}': {rendered},")
        lines.append(f"{indent}}}")
        return '\n'.join(lines)

    def _render_payload_list(self, items: list[PayloadEntry], indent_level: int) -> str:
        indent = ' ' * (indent_level * 4)
        inner_indent = ' ' * ((indent_level + 1) * 4)
        lines = ['[']
        for entry in items:
            rendered = self._render_entry(entry, indent_level + 1)
            if '\n' in rendered:
                rendered = rendered.replace('\n', '\n' + inner_indent)
            lines.append(f"{inner_indent}{rendered},")
        lines.append(f"{indent}]")
        return '\n'.join(lines)

    def create(self):
        payload = ''
        if self.payload:
            # noinspection PyTypeChecker
            payload_body = self._render_payload_dict(self.payload, 2)
            payload = f"""
    payload = {payload_body}
    """
        payload_parameter = f', {self.payload_type}=payload' if self.payload else ''

        result = f"""
def {self.name}(self):
    url = {self.url}
    
    headers = {{
{'\n'.join(f"        '{key}': {value}," for key, value in self.headers.items() if key != 'Content-Length')}
    }}
{payload}
    response = self.session.{self.request.method.lower()}(url, headers=headers{payload_parameter})
{'\n' + '\n'.join(f'    {line}' for line in self.results) if self.results else ''}"""

        return result


class Continue(Exception):
    pass


class Scriptor(ElementTree):
    def __init__(self, file, keyword):
        super().__init__(file=file)
        self.keyword = keyword
        self.analyzed: list[Request] = list()
        self.functions: dict[int, Function] = dict()
        self.recorded_references = dict()
        self.constructor_lines = list()
        self._root = self.getroot()
        items = self._root.findall('item')
        self.requests: list[Request] = list()
        for i in range(len(items)): self.requests.append(Request(i, items[i]))
        Path('./static').mkdir(exist_ok=True)

    @staticmethod
    def _iter_assignment_segments(value: str):
        pattern = re.compile(r'([A-Za-z0-9._-]+)\s*=\s*([^,;]+)')
        for match in pattern.finditer(value):
            sub_key = match.group(1)
            sub_value = match.group(2).strip()
            key_start, key_end = match.span(1)
            value_start, value_end = match.span(2)
            yield {
                'key': sub_key,
                'value': sub_value,
                'key_start': key_start,
                'key_end': key_end,
                'value_start': value_start,
                'value_end': value_end,
            }

    def _create_regex_reference(self, request: Request, pattern_key: str, pattern_value: str, original_value: str):
        var_name = to_snake_case(pattern_key)
        line = rf"""self.{var_name} = re.search(r'{pattern_value}', response.text).group(1)"""
        function = self.functions[request.index]
        if line not in function.results:
            function.results.append(line)
        constructor_line = f'self.{var_name} = None'
        if constructor_line not in self.constructor_lines:
            self.constructor_lines.append(constructor_line)
        reference = f'self.{var_name}'
        self.recorded_references[original_value] = reference
        return reference

    def _resolve_simple_value(self, value: str, request: Request):
        if value in self.recorded_references:
            return self.recorded_references[value]

        new_request = self.track(value)
        if not new_request:
            return None

        if new_request.index not in self.functions:
            self.functions[new_request.index] = Function(new_request)

        if new_request not in self.analyzed:
            print(f'Analyzing {new_request.index} - {new_request.url}')
            self.analyzed.append(new_request)
            self.analyse(new_request)

        if value in self.recorded_references:
            return self.recorded_references[value]

        response = new_request.response
        response_headers_lines = response.split('\n\n', 1)[0].split('\n')[1:]
        response_headers = dict()
        response_cookies = dict()
        for line in response_headers_lines:
            h_key, h_value = line.split(': ', 1)
            if h_key == 'Set-Cookie':
                c_key, c_value = h_value.split('; ')[0].split('=', 1)
                response_cookies[c_key] = c_value
            else:
                response_headers[h_key] = h_value

        if value in response_cookies.values():
            c_name = next((k for k, v in response_cookies.items() if v == value))
            reference = f'self.session.cookies.get("{c_name}")'
            self.recorded_references[value] = reference
            return reference

        if value in response_headers.values():
            self.response_headers_reference(new_request, response_headers, value)
            return self.recorded_references.get(value)

        response_body = response.split('\n\n', 1)
        body_text = response_body[1] if len(response_body) > 1 else ''
        pattern_key, pattern_value = generate_generic_pattern(body_text, value)
        if pattern_key:
            return self._create_regex_reference(new_request, pattern_key, pattern_value, value)

        return None

    def _handle_header_partial(self, function: Function, header_key: str, header_value: str, request: Request) -> bool:
        handled = False
        parts: list[str] = []
        cursor = 0
        for segment in self._iter_assignment_segments(header_value):
            key_start = segment['key_start']
            key_end = segment['key_end']
            value_start = segment['value_start']
            value_end = segment['value_end']
            sub_key = segment['key']
            sub_value = segment['value']

            value_expr = self._resolve_simple_value(sub_value, request)
            key_expr = self._resolve_simple_value(sub_key, request)

            if not value_expr and not key_expr:
                continue

            if cursor < key_start:
                parts.append(repr(header_value[cursor:key_start]))

            if key_expr:
                parts.append(key_expr)
            else:
                parts.append(repr(header_value[key_start:key_end]))

            if key_end < value_start:
                parts.append(repr(header_value[key_end:value_start]))

            if value_expr:
                parts.append(value_expr)
            else:
                parts.append(repr(header_value[value_start:value_end]))

            cursor = value_end
            handled = True

        if handled:
            if cursor < len(header_value):
                parts.append(repr(header_value[cursor:]))
            expression = ' + '.join(parts)
            function.headers[header_key] = expression if parts else repr(header_value)
        return handled

    @staticmethod
    def _sanitize_filename(part: str) -> str:
        safe = re.sub(r'[^A-Za-z0-9._-]+', '_', part)
        return safe or 'segment'

    def start_point(self):
        for request in self.requests:
            if self.keyword in (request.request + (request.response if request.response else '')):
                return request
        return None

    def analyse(self, request: Request):
        # URL
        url_parameters = {k: v[0] for k, v in parse_qs(urlparse(request.url).query).items()}
        self.extract(url_parameters, 'url', request)

        # Header
        # noinspection PyUnresolvedReferences
        headers_str = request.request.split('\n\n', 1)[0].split('\n', 1)[1]
        headers = {k: v for k, v in (header.split(': ') for header in headers_str.split('\n'))}
        self.extract(headers, 'headers', request)

        # Cookie
        if cookie := headers.get('Cookie'):
            cookies = {k: v for k, v in (cookie.split('=', 1) for cookie in cookie.split('; '))}
            self.extract(cookies, 'cookies', request)

        # Payload
        function = self.functions[request.index]
        if function.payload:
            self.extract_payload(request, function)

    def extract(self, values, role, request):
        variable = classify_url_params(values)
        for key, value in values.items():
            # If the value is variable
            if variable[key]:
                # The function of the current request
                function = self.functions[request.index]

                if role == 'headers' and '=' in value:
                    if self._handle_header_partial(function, key, value, request):
                        continue

                # If value is already found
                if value in self.recorded_references:
                    if role == 'url':
                        # Turn the url string to f-string
                        if not function.url.startswith('f'):
                            function.url = f'f{function.url}'

                        # replace the value by its corresponding variable saved earlier
                        function.url = function.url.replace(value, f"""{{{self.recorded_references[value]}}}""")

                    elif role == 'headers':
                        # Replace the header with its corresponding variable saved earlier
                        function.headers[key] = self.recorded_references[value]
                        continue

                    elif role == 'cookies':
                        pass  # Do nothing

                    elif role == 'payload':
                        function.set_payload_expression((key,), self.recorded_references[value])

                    continue

                new_request = self.track(value)
                if not new_request:
                    if new_request := self.track(key):
                        # noinspection PyUnresolvedReferences
                        safe_key = self._sanitize_filename(str(key))
                        tail = new_request.url.split('/')[-1] if new_request.url else ''
                        safe_tail = self._sanitize_filename(tail or 'response')
                        output_path = Path('./static') / f'_{safe_key}_{safe_tail}'
                        output_path.write_text(new_request.response, encoding='utf-8', errors='ignore')
                    continue

                if new_request.index not in self.functions:
                    self.functions[new_request.index] = Function(new_request)

                if new_request not in self.analyzed:
                    print(f'Analyzing {new_request.index} - {new_request.url}')
                    self.analyzed.append(new_request)
                    self.analyse(new_request)

                # Extract headers and cookies
                response_headers_lines = new_request.response.split('\n\n', 1)[0].split('\n')[1:]
                response_headers = dict()
                response_cookies = dict()
                for line in response_headers_lines:
                    h_key, h_value = line.split(': ', 1)
                    if h_key == 'Set-Cookie':
                        c_key, c_value = h_value.split('; ')[0].split('=', 1)
                        response_cookies[c_key] = c_value
                    else:
                        response_headers[h_key] = h_value

                if role == 'url':
                    if value in response_cookies.values():
                        c_name = next((k for k, v in response_cookies.items() if v == value))
                        self.recorded_references[value] = f'self.session.cookies.get("{c_name}")'
                        if not function.url.startswith('f'):
                            function.url = f'f{function.url}'
                        function.url = function.url.replace(value, f"""{{{self.recorded_references[value]}}}""")
                        continue
                    if value in response_headers.values():
                        self.response_headers_reference(new_request, response_headers, value)
                        if not function.url.startswith('f'):
                            function.url = f'f{function.url}'
                        function.url = function.url.replace(value, f"""{{{self.recorded_references[value]}}}""")
                        continue

                elif role == 'headers':
                    try:
                        self.handle_cookies_and_headers(
                            value, response_cookies, function, 'headers', key, response_headers, new_request)
                    except Continue:
                        continue

                elif role == 'cookies':
                    if value in response_cookies.values():
                        c_name = next((k for k, v in response_cookies.items() if v == value))
                        self.recorded_references[value] = f'self.session.cookies.get("{c_name}")'
                        continue
                    if value in response_headers.values():
                        h_name = next(k for k, v in response_headers.items() if v == value)
                        line = f"""self.session.cookies.set("{key}", response.headers.get("{h_name}"))"""
                        self.functions[new_request.index].results.append(line)
                        self.recorded_references[value] = f"""self.session.cookies.get("{key}")"""
                        continue

                elif role == 'payload':
                    try:
                        self.handle_cookies_and_headers(
                            value, response_cookies, function, 'payload', (key,), response_headers, new_request)
                    except Continue:
                        continue

                pattern_key, patter_value = generate_generic_pattern(new_request.response.split('\n\n', 1)[1], value)

                if pattern_key:
                    self.recorded_references[value] = f'self.{to_snake_case(pattern_key)}'
                    desired_value = fr"""re.search(r'{patter_value}', response.text).group(1)"""
                    if role == 'url':
                        line = rf"""self.{to_snake_case(pattern_key)} = {desired_value}"""
                        self.functions[new_request.index].results.append(line)
                        self.constructor_lines.append(f'self.{to_snake_case(pattern_key)} = None')
                        self.recorded_references[value] = f'self.{to_snake_case(pattern_key)}'
                        if not function.url.startswith('f'):
                            function.url = f'f{function.url}'
                        function.url = function.url.replace(value, f'{{{self.recorded_references[value]}}}')
                        continue

                    if role == 'headers':
                        self.handle_regex(
                            pattern_key, desired_value, new_request, value, function, 'headers', key)
                        continue

                    if role == 'cookies':
                        line = rf"""self.session.cookies.set("{key}", {desired_value})"""
                        self.functions[new_request.index].results.append(line)
                        self.recorded_references[value] = f"""self.session.cookies.get("{key}")"""
                        continue

                    if role == 'payload':
                        self.handle_regex(
                            pattern_key, desired_value, new_request, value, function, 'payload', (key,))
                        continue

    def extract_payload(self, request: Request, function: Function):
        for path, entry in function.iter_payload_leaves():
            key_label = str(path[-1])
            raw_value = entry.original if entry.original is not None else entry.value
            if raw_value is None:
                continue
            value_str = raw_value if isinstance(raw_value, str) else str(raw_value)
            variable = classify_url_params({key_label: value_str})[key_label]
            if not variable:
                continue

            if value_str in self.recorded_references:
                function.set_payload_expression(path, self.recorded_references[value_str])
                continue

            new_request = self.track(value_str)
            if not new_request:
                continue

            if new_request.index not in self.functions:
                self.functions[new_request.index] = Function(new_request)

            if new_request not in self.analyzed:
                print(f'Analyzing {new_request.index} - {new_request.url}')
                self.analyzed.append(new_request)
                self.analyse(new_request)

            response_headers_lines = new_request.response.split('\n\n', 1)[0].split('\n')[1:]
            response_headers = dict()
            response_cookies = dict()
            for line in response_headers_lines:
                h_key, h_value = line.split(': ', 1)
                if h_key == 'Set-Cookie':
                    c_key, c_value = h_value.split('; ')[0].split('=', 1)
                    response_cookies[c_key] = c_value
                else:
                    response_headers[h_key] = h_value

            try:
                self.handle_cookies_and_headers(
                    value_str, response_cookies, function, 'payload', path, response_headers, new_request)
            except Continue:
                continue

            pattern_key, pattern_value = generate_generic_pattern(
                new_request.response.split('\n\n', 1)[1], value_str)

            if pattern_key:
                desired_value = fr"re.search(r'{pattern_value}', response.text).group(1)"
                self.handle_regex(
                    pattern_key, desired_value, new_request, value_str, function, 'payload', path)

    def response_headers_reference(self, new_request, response_headers, value):
        h_name = next(k for k, v in response_headers.items() if v == value)
        var_name = to_snake_case(h_name)
        line = f"""self.{var_name} = response.headers.get('{h_name}')"""
        self.functions[new_request.index].results.append(line)
        line = f"""self.{var_name} = None"""
        self.constructor_lines.append(line)
        self.recorded_references[value] = f'self.{var_name}'

    def track(self, param):
        pattern = rf'(?<!\w){re.escape(str(param))}(?!\w)'
        for request in self.requests:
            if request.response and re.search(pattern, request.response):
                return request
        return None

    def create(self):
        start = self.start_point()
        self.analyzed.append(start)
        self.functions[start.index] = Function(start)
        self.analyse(start)
        functions = [self.functions[i].create() for i in sorted(self.functions)]
        # noinspection PyTypeChecker
        needs_json = any(self.functions[i].requires_json for i in self.functions)
        imports = ['import re']
        if needs_json:
            imports.append('import json')
        imports.append('from threading import Thread')
        imports_block = '\n'.join(imports)

        body = f"""
from colorama import Fore, init
from requests import Session

from autowebx import sync_print, exception_line, int_input, handle_threads
from autowebx.auto_save_dict import AutoSaveDict
from autowebx.files import load
from autowebx.remotix import Run


class Task(Thread):
    def __init__(self, count: int = 0):
        super().__init__()
        self.count = count
        self.name = f'Task_{{self.count}}'
        self.session = Session()
{'\n'.join(f'        {line}' for line in self.constructor_lines)}
{'\n'.join(function.replace('\n','\n    ') for function in functions)}
    def run(self):
        try:
{'\n'.join(f'            self.{self.functions[i].name}()' for i in sorted(self.functions))}
        except Exception as e:
            sync_print(f'{{Fore.RED}}[{{self.count}}] {{e.__class__.__name__}}: {{e}} ({{exception_line()}}){{Fore.RESET}}')

if __name__ == '__main__':
    try:
        init()
        threads = int_input('Threads: ')
        total = int_input('Total: ')
        proxy_enable = int_input('Proxy enable? (1/0): ', 0) == 1
        files = ['data.json']

        if proxy_enable:
            proxies = load('proxy.txt')
            files.append('proxy.txt')

        asd = AutoSaveDict('data.json')

        run = Run("<API-KEY>", {{
            'threads': threads,
            'total': total,
            'proxy_enable': proxy_enable,
        }}, *files)

        handle_threads(threads, total, Task)

        run.done()
    except Exception as er:
        sync_print(f'{{Fore.RED}}{{er.__class__.__name__}}: {{er}} ({{exception_line()}}){{Fore.RESET}}')
"""
        result = f"{imports_block}\n\n{body}"
        open('./static/main3.py', 'w').write(result)



    def handle_cookies_and_headers(
            self, value, response_cookies, function, destination, key, response_headers, new_request
    ):
        if destination == 'headers':
            setter = lambda expr: function.headers.__setitem__(key, expr)
        elif destination == 'payload':
            setter = lambda expr: function.set_payload_expression(key, expr)
        else:
            setter = lambda expr: None

        if value in response_cookies.values():
            c_name = next((k for k, v in response_cookies.items() if v == value))
            reference = f'self.session.cookies.get("{c_name}")'
            self.recorded_references[value] = reference
            setter(reference)
            raise Continue()
        if value in response_headers.values():
            self.response_headers_reference(new_request, response_headers, value)
            reference = self.recorded_references[value]
            setter(reference)
            raise Continue()


    def handle_regex(self, pattern_key, desired_value, new_request, value, function, destination, key):
        if destination == 'payload':
            setter = lambda expr: function.set_payload_expression(key, expr)
        elif destination == 'headers':
            setter = lambda expr: function.headers.__setitem__(key, expr)
        else:
            setter = lambda expr: None
        line = rf"""self.{to_snake_case(pattern_key)} = {desired_value}"""
        self.functions[new_request.index].results.append(line)
        self.constructor_lines.append(f'self.{to_snake_case(pattern_key)} = None')
        self.recorded_references[value] = f'self.{to_snake_case(pattern_key)}'
        setter(self.recorded_references[value])


if __name__ == '__main__':
    Scriptor('case_zurich.xml', '1667819827').create()
