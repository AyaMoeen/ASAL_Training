import pytest
from HTML.HTMLElement import HTMLElement
@pytest.fixture
def fixture_element():
    element1 = HTMLElement('h1', value='Ayosh', attrs={'id': 'id1', 'class': 'myClass'})
    element2 = HTMLElement('h2', value='backend training', attrs={'id': 'id2'})
    element3 = HTMLElement('div', value='test', attrs={'id': 'id3'})
    return element1, element2, element3

def test_init(fixture_element) -> None:
    element1, _, _ = fixture_element
    assert element1.name == 'h1'
    assert element1.attrs['id'] == 'id1'
    

def test_init_invalid_tag() -> None:
    with pytest.raises(Exception) as e:
        HTMLElement('invalid_tag', value='test of invalid tag', attrs={'id': 'id1'})
    assert str(e.value) == "invalid_tag not vaild name of tag in the HTML"

def test_init_invalid_param():
    with pytest.raises(Exception):
        HTMLElement('div', value=1, attrs=['id'])
    
def test_append(fixture_element) -> None:
    element1, element2, _ = fixture_element
    HTMLElement.append(element1, element2)
    assert element2 in element1.value
    
def test_append_negative(fixture_element) -> None:
    element1, _, _ = fixture_element
    element2 = HTMLElement('p', value='backend training', attrs={'id': 'id1', 'class': 'parag'})
    with pytest.raises(Exception) as e:
        HTMLElement.append(element1, element2)
    assert str(e.value) == "Duplicate ID, Faild to append"
    
def test_render(fixture_element) -> None:
    element1, _, _ = fixture_element
    assert HTMLElement.render(element1) == '<h1 id="id1" class="myClass">Ayosh\n</h1>\n'
    
def test_render_negative_style(fixture_element) -> None:
    element1, _, _ = fixture_element
    print(HTMLElement.render(element1))
    assert HTMLElement.render(element1) != '<h1 id="id1 class="myClass">Ayosh</h1>'
 
def test_find_element_by_tag_name(fixture_element) -> None:
    element1, element2, element3 = fixture_element
    HTMLElement.append(element1, element2)
    HTMLElement.append(element2, element3)
    html:list = HTMLElement.find_element_by_tag_name(element1, 'h2')
    a:'HTMLElement'= html[0]
    assert a.name =='h2'

def test_find_element_by_attrs(fixture_element) -> None:
    element1, _, _ = fixture_element
    html:list = HTMLElement.find_element_by_attrs(element1, 'id', 'id1')
    a:'HTMLElement'= html[0]
    assert a.attrs['id'] =='id1'
    assert a.attrs['class'] =='myClass'
    
def test_remove(fixture_element) -> None:
    _, element2, element3 = fixture_element
    root = HTMLElement('div', value=[element2,element3], attrs={'id': 'root', 'class': 'myClass'})
    HTMLElement.remove(root,element2)
    assert len(root.value) == 1

def test_clone(fixture_element) -> None:
    element1, _, _ = fixture_element
    result_clone = HTMLElement.clone(element1.parent, element1)
    assert result_clone.attrs['id'].startswith('id1_clone')

def test_to_dict(fixture_element) -> None:
    element1, _, _ = fixture_element
    element_dict = element1.to_dict()
    assert isinstance(element_dict, dict)

    
def test_from_dict() -> None:
    dict_element = {
        "name": "h1",
        "value": "Ayosh",
        "attrs": {
          "id": "id1"
        },
        "children": []
    }
    element_html = HTMLElement.from_dict(dict_element)
    assert isinstance(element_html, HTMLElement)
    
def test_check_update_id(fixture_element):
    element1, element2, element3 = fixture_element
    HTMLElement.append(element1, element2)
    assert element1.check_update_id(element1.attrs['id']) is True
    assert element1.check_update_id(element2.attrs['id']) is True
    assert element1.check_update_id(element3.attrs['id']) is False

def test_render_html_file(fixture_element):
    element1, element2, _ = fixture_element
    assert HTMLElement.render_html_file(element1) == '<!DOCTYPE html>\n<html>\n    <h1 id="id1" class="myClass">Ayosh\n    </h1>\n</html>\n'
    
    
