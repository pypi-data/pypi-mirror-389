from typing import Union
import os
import json

def read_jsonl(file):
    df = []
    with open(file, mode='r', encoding='utf-8') as reader:
        line = reader.readline()
        while line:
            obj = json.loads(line)
            df.append(obj)
            line = reader.readline()
    return df

def write_jsonl(obj_list: Union[dict, list[dict]], file: str, force=False, silent=False):
    if not isinstance(file, str):
        raise TypeError("file must be str, got {}".format(type(file).__name__))

    if os.path.exists(file) and force == False:
        print('[INFO] {} already exists.'.format(file))
        return
    
    dir_path = os.path.dirname(file)
    if dir_path != '':
        os.makedirs(dir_path, exist_ok=True)
    

    if isinstance(obj_list, dict):
        obj_list = [obj_list]
    with open(file, mode='w', encoding='utf-8') as fp:
        for obj in obj_list:
            json.dump(obj, fp, ensure_ascii=False)
            print(file=fp)
    
    if not silent:
        print('[INFO] save to {}'.format(file))


def append_jsonl(obj_list: Union[dict, list[dict]], file: str) -> None:
    if not isinstance(file, str):
        raise TypeError("file must be str, got {}".format(type(file).__name__))

    if isinstance(obj_list, dict):
        obj_list = [obj_list]
    with open(file, mode='a', encoding='utf-8') as fp:
        for obj in obj_list:
            json.dump(obj, fp, ensure_ascii=False)
            print(file=fp)