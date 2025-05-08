import pytest
import pandas as pd
from pathlib import Path
from src.data_management.sku_mapper import SkuMapper

@pytest.fixture
def sample_mapping_file(tmp_path):
    """Create a temporary mapping file for testing."""
    mapping_data = {
        'SKU': ['ABC-123', 'DEF-456', 'GHI-789'],
        'MSKU': ['MSKU-001', 'MSKU-002', 'MSKU-003']
    }
    df = pd.DataFrame(mapping_data)
    file_path = tmp_path / "test_mapping.csv"
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def sku_mapper(sample_mapping_file):
    """Create a SkuMapper instance for testing."""
    return SkuMapper(sample_mapping_file)

def test_sku_validation(sku_mapper):
    """Test SKU format validation."""
    # Valid SKUs
    assert sku_mapper.validate_sku('ABC-123')
    assert sku_mapper.validate_sku('DEF-456')
    
    # Invalid SKUs
    assert not sku_mapper.validate_sku('ABC123')  # Missing hyphen
    assert not sku_mapper.validate_sku('ABC-12')  # Too short
    assert not sku_mapper.validate_sku('abc-123')  # Lowercase

def test_sku_mapping(sku_mapper):
    """Test SKU to MSKU mapping."""
    # Valid mappings
    assert sku_mapper.map_sku('ABC-123') == 'MSKU-001'
    assert sku_mapper.map_sku('DEF-456') == 'MSKU-002'
    
    # Invalid SKU format
    assert sku_mapper.map_sku('ABC123') is None
    
    # Unknown SKU
    assert sku_mapper.map_sku('XYZ-789') is None

def test_process_dataframe(sku_mapper):
    """Test DataFrame processing."""
    # Create test data
    data = {
        'OrderID': ['ORD001', 'ORD002', 'ORD003'],
        'SKU': ['ABC-123', 'DEF-456', 'XYZ-789']
    }
    df = pd.DataFrame(data)
    
    # Process DataFrame
    result = sku_mapper.process_dataframe(df, 'SKU')
    
    # Check results
    assert 'MSKU' in result.columns
    assert result.loc[0, 'MSKU'] == 'MSKU-001'
    assert result.loc[1, 'MSKU'] == 'MSKU-002'
    assert pd.isna(result.loc[2, 'MSKU'])  # Unknown SKU

def test_invalid_column(sku_mapper):
    """Test handling of invalid column name."""
    df = pd.DataFrame({'OrderID': ['ORD001'], 'SKU': ['ABC-123']})
    
    with pytest.raises(ValueError):
        sku_mapper.process_dataframe(df, 'InvalidColumn')

def test_multiple_skus(sku_mapper):
    """Test mapping multiple SKUs at once."""
    skus = ['ABC-123', 'DEF-456', 'XYZ-789']
    results = sku_mapper.map_skus(skus)
    
    assert results['ABC-123'] == 'MSKU-001'
    assert results['DEF-456'] == 'MSKU-002'
    assert results['XYZ-789'] is None 