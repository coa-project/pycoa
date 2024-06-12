#to run all tests.
#pytest tests/test_front.py
#to run a specific test
#pytest tests/test_front.py::test_listwhat

import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coa.front import *
from coa.allvisu import *
from coa.dbparser import _db_list_dict

# Création d'une fixture pour instancier la classe Front
@pytest.fixture
def front_instance():
    return Front()

# ------------------------- test whattoso ------------------------------
def test_whattodo(front_instance):
    """Test the whattodo method."""
    result = front_instance.whattodo()
    assert not result.empty, "whattodo should return a non-empty DataFrame"

# ------------------------- test set visu ------------------------------
def test_setvisu(front_instance, **kwargs):
    """Test the setvisu method with valid inputs."""
    # valid input
    front_instance.setvisu(vis='bokeh')
    assert front_instance.getdisplay() == 'bokeh'

# ------------------------- test setvisu with invalid vis ---------------------
def test_invalid_setvisu(front_instance):
    """Test the setvisu method with invalid inputs."""
    # invalid input
    with pytest.raises(Exception) as excinfo:
        front_instance.setvisu(vis='invalid_visu')
    assert "Sorry but invalid_visu visualisation isn't implemented" 

# ------------------------- test getdisplay ------------------------------
def test_getdisplay(front_instance):
    """Test the getdisplay method."""
    front_instance.setvisu(vis='mplt')
    assert front_instance.getdisplay() == 'mplt'


############################   START TEST LIST  #########################

# ------------------------- test listoutput ------------------------------
def test_listoutput(front_instance):
    """Test the listoutput method."""
    expected_result = ['pandas', 'geopandas', 'list', 'dict', 'array']
    result = front_instance.listoutput()
    assert isinstance(result, list), "listoutput should return a list"
    assert result == expected_result, f"List output should return :'{expected_result}', but returned :'{result}'"

# ------------------------- test listvisu ------------------------------
def test_listvisu(front_instance):
    """Test the listvisu method."""
    expected_result = ['bokeh', 'folium', 'seaborn', 'mplt']
    result = front_instance.listvisu()
    assert result == expected_result, f"listvisu should return : :'{expected_result}', but returned :'{result}'"

# ------------------------- test listwhom ------------------------------
def test_listwhom(front_instance):
    """Test the listwhom method."""
    real_length = len(_db_list_dict)
    result = front_instance.listwhom()
    assert isinstance(result, list), "listwhom should return a list"
    assert len(result) == real_length, f"listwhom should return:'{real_length}', but returned :'{len(result)}'"

# ------------------------- test listwhat ------------------------------
def test_listwhat(front_instance):
    """Test the listwhat method."""
    result = front_instance.listwhat()
    assert isinstance(result, list), "listwhat should return a list"
    assert 'weekly' in result, "'weekly' should be in the list returned by listwhat"
    assert 'daily' in result, "'daily' should be in the list returned by listwhat"

# ------------------------- test listplot ------------------------------
def test_listhist(front_instance):
    """Test the listhist method."""
    expected_result = ['bylocation', 'byvalue', 'pie']
    result = front_instance.listhist()
    assert isinstance(result, list), "listhist should return a list"
    assert result == expected_result, f"listhist should return :'{expected_result}', but returned :'{result}'"

# ------------------------- test listplot ------------------------------
def test_listplot(front_instance):
    """Test the listplot method."""
    expected_result = ['date', 'menulocation', 'versus', 'spiral', 'yearly']
    result = front_instance.listplot()
    assert isinstance(result, list), "listplot should return a list"
    assert result == expected_result, f"listplot should return :'{expected_result}', but returned :'{result}'"

# ------------------------- test listoption ------------------------------
def test_listoption(front_instance):
    """Test the listoption method."""
    expected_result = ['nonneg', 'nofillnan', 'smooth7', 'sumall']
    result = front_instance.listoption()
    assert isinstance(result, list), "listoption should return a list"
    assert result == expected_result, f"listoption should return :'{expected_result}', but returned :'{result}'"

# ------------------------- test listchartkargs ------------------------------
def test_listchartkargs(front_instance):
    """Test the listchartkargs method."""
    result = front_instance.listchartkargs()
    assert isinstance(result, list), "listchartkargs should return a list"
    assert len(result) == 13, "listchartkargs should return 13 elements"

# ------------------------- test listtile ------------------------------
def test_listtile(front_instance):
    """Test the listtile method."""
    expected_result = ['openstreet','esri','stamen']
    result = front_instance.listtile()
    assert isinstance(result, list), "listtile should return a list"
    assert result == expected_result, "listtile should return ['openstreet','esri','stamen']"

# ------------------------- test listbypop ------------------------------
def test_listbypop(front_instance):
    expected_result = ['no', '100', '1k', '100k', '1M', 'pop']
    result = front_instance.listbypop()
    assert isinstance(result, list), "listbypop should return a list"
    assert result == expected_result, "listbypop should return ['bylocation','byvalue']"

# ------------------------- test listmaplabel ------------------------------
def test_listmaplabel(front_instance):
    expected_result = ['text','textinteger','spark','label%','log','unsorted','exploded','dense']
    result = front_instance.listmaplabel()
    assert isinstance(result, list), "listmaplabel should return a list"
    assert result == expected_result, f"listmaplabel should return :'{expected_result}', but returned :'{result}'"

###################  END TEST LIST  ####################


####START TEST SETWHOM ET GETWHOM####

# ------------------------- test setwhom ------------------------------
def test_setwhom_valid_base(front_instance):
    """Test setwhom with a valid base name"""
    base = 'govcy'  
    front_instance.setwhom(base, reload=True)
    assert front_instance.getwhom() == base, f"Expected base to be '{base}', but got '{front_instance.getwhom()}'"

# ------------------------- test setwhom with invalid base --------------------------
def test_setwhom_invalid_base(front_instance):
    """Test setwhom with an invalid base name"""
    base = 'invalid_base'
    with pytest.raises(Exception) as excinfo:
        front_instance.setwhom(base, reload=True)
    assert "is not a supported database" in str(excinfo.value)

# ------------------------- test setwhom with invalid boolean ---------------------------
def test_setwhom_reload_invalid_type(front_instance):
    """Test front_instance.setwhom with an invalid type for reload"""
    base = 'govcy'
    with pytest.raises(Exception) as excinfo:
        front_instance.setwhom(base, reload="not_a_boolean")
    assert "reload must be a boolean" in str(excinfo.value)
    
# ------------------------- test getwhom -----------------------------------------
def test_getwhom_base_set(front_instance):
    """Test getwhom after a base has been set"""
    base = 'govcy'  
    front_instance.setwhom(base, reload=True)
    result = front_instance.getwhom()
    assert result == base, f"Expected base to be '{base}', but got '{result}'"

# ------------------------- test getwhom without base set ------------------------------
def test_getwhom_no_base_set(front_instance):
    """Test getwhom when no base is set"""
    result = front_instance.getwhom()
    assert result == '', "Expected an empty string when no base is set"


# ------------------------- test getwhom error -----------------------------------------
def test_getwhom_with_error(front_instance):
    """Test getwhom when no base is set and return_error is True"""
    _db = ''
    _whom = ''
    def getwhom(return_error=True):
        if '_db' not in globals() or _db is None:
            if return_error:
                raise Exception('setwhom MUST be defined first !')
            else:
                return ''
        else:
            return _whom

    with pytest.raises(Exception) as excinfo:
        getwhom(return_error=True)
    assert "setwhom MUST be defined first" in str(excinfo.value)

########################  END TEST SETWHOM ET GETWHOM  ########################

#getkeywordinfo
def test_getkeywordinfo(front_instance):
    """Test the getkeywordinfo method with a valid keyword."""
    front_instance.setwhom('govcy', reload=False)
    valid_keyword = 'cur_hosp'
    result = front_instance.getkeywordinfo(valid_keyword)
    assert "number of patients with covid-19 hospitalized cases (Hospitalised Cases)"

###############################  TEST GET  ###############################
# ------------------------- test get with pandas -----------------------------------------
def test_get_pandas(front_instance):
    """Test the get method with output as pandas."""
    front_instance.setwhom('govcy', reload=False)
    result = front_instance.get(output='pandas')
    assert isinstance(result, pd.DataFrame), "Output should be a pandas DataFrame"

# ------------------------- test get with geopandas --------------------------------------
def test_get_geopandas(front_instance):
    """Test the get method with output as geopandas."""
    front_instance.setwhom('govcy', reload=False)
    #rajouter un test pour la colonne geometry    
    result = front_instance.get(output='geopandas')
    assert isinstance(result, gpd.GeoDataFrame), "Output should be a GeoDataFrame"

# ------------------------- test get with dict ------------------------------------------
def test_get_dict(front_instance):
    """Test the get method with output as dict."""
    front_instance.setwhom('govcy', reload=False)
     #rajouter un test sur dictionnaire     
    result = front_instance.get(output='dict')
    assert isinstance(result, dict), "Output should be a dict"

# ------------------------- test get with list ------------------------------------------
def test_get_list(front_instance):
    """Test the get method with output as list."""
    front_instance.setwhom('govcy', reload=False)
    result = front_instance.get(output='list')
    assert isinstance(result, list), "Output should be a list"

# ------------------------- test get with array------------------------------------------
def test_get_array(front_instance):
    """Test the get method with output as array."""
    front_instance.setwhom('govcy', reload=False)
    result = front_instance.get(output='array')
    assert isinstance(result, np.ndarray), "Output should be a numpy array"

# ------------------------- test get with invalid output ----------------------------------
def test_get_invalid_output(front_instance):
    """Test the get method with an invalid output."""
    front_instance.setwhom('govcy', reload=False)
    with pytest.raises(CoaKeyError):
        front_instance.get(output='invalid')

# ------------------------- test get with where ------------------------------------------
def test_get_where(front_instance):
    """Test the get method with filtering by 'where' for the 'spf' database."""
    front_instance.setwhom('spf', reload=False)
    result = front_instance.get(where='Paris', output='pandas')
    
    assert isinstance(result, pd.DataFrame), "Output should be a pandas DataFrame"
    assert not result.empty, "Resulting DataFrame should not be empty"
    assert all(result['where'] == 'Paris'), "All rows should have where == 'Paris'"

# ------------------------- test get with which ------------------------------------------
def test_get_which(front_instance):
    """Test the get method with filtering by 'which' for the 'spf' database."""
    front_instance.setwhom('spf', reload=False)
    result = front_instance.get(where='Paris', which='cur_hosp', output='pandas')
    
    assert isinstance(result, pd.DataFrame), "Output should be a pandas DataFrame"
    assert not result.empty, "Resulting DataFrame should not be empty"
    assert 'cur_hosp' in result.columns, "The DataFrame should contain a 'cur_hosp' column"
