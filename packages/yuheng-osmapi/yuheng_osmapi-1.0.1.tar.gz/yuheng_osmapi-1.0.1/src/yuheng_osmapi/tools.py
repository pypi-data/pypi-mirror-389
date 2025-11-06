import yuheng
from yuheng import logger


def transform_tag_xml(tag: dict):
    paragraph = ""
    for key, value in tag.items():
        single_line = f'<tag k="{key}" v="{value}"/>\n'
        paragraph += single_line

    return paragraph


def parse_result(result: str) -> yuheng.Carto:
    single_element_world = yuheng.Carto()
    single_element_world.read(mode="memory", text=str(result))
    return single_element_world


def get_attribute_from_world(
    node_dict: dict, attribute: str = "version"
) -> int:
    attribute_list = []
    for id, obj in node_dict.items():
        if attribute == "version":
            attribute_list.append(obj.version)
        if attribute == "lat":
            attribute_list.append(obj.lat)
        if attribute == "lon":
            attribute_list.append(obj.lon)
    logger.debug(attribute_list)
    return attribute_list[0]
