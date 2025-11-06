"""
Copyright (c) 2025 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: sushant.mhambrey@teradata.com
Secondary Owner: PankajVinod.Purandare@Teradata.com

This module contains utility functions for Langchain Document objects.
"""  
from langchain_core.documents import Document
from teradataml.utils.internal_buffer import _InternalBuffer
from teradataml.utils.validators import _Validators
from teradataml.common.utils import UtilFuncs
from teradataml import list_td_reserved_keywords
from teradataml.utils.dtypes import _ListOf

def rename_metadata_keys(docs, key_mapping=None, prefix=None):
    """
    DESCRIPTION:
        Renames metadata keys in Langchain Document objects. Either a key mapping
        dictionary or a prefix for reserved keywords must be provided, but not both.
    
    PARAMETERS:
        docs:
            Required Argument.
            Specifies the document(s) whose metadata keys should be renamed.
            Types: Langchain Document object or list of Langchain Document objects.
        
        key_mapping:
            Optional Argument.
            Specifies a dictionary mapping old key names to new key names.
            Types: dict
            Example: {"old_key": "new_key", "source": "doc_source"}
        
        prefix:
            Optional Argument.
            Specifies a prefix to add to reserved keyword metadata keys.
            Types: str
            Example: "doc_"
    
    RETURNS:
        list of modified Langchain Document objects
    
    RAISES:
        TeradataMlException: If both or neither key_mapping and prefix are provided.
    
    EXAMPLES:
        # Example 1: Using key_mapping
        >>> from langchain_core.documents import Document
        >>> docs = [Document(page_content="Sample", metadata={"source": "file.pdf"})]
        >>> renamed_docs = rename_metadata_keys(docs, key_mapping={"source": "doc_source"})
        
        # Example 2: Using prefix for reserved keywords
        >>> docs = [Document(page_content="Sample", metadata={"table": "data"})]
        >>> renamed_docs = rename_metadata_keys(docs, prefix="doc_")
    """    
    # Validate the arguments.
    arg_info_matrix = [
        ["docs", docs, True, (_ListOf(Document), Document), True,],
        ["key_mapping", key_mapping, True, (dict), True,],
        ["prefix", prefix, True, (str), True,],
    ]

    _Validators._validate_missing_required_arguments(arg_info_matrix)
    _Validators._validate_function_arguments(arg_info_matrix)

    # Validate that exactly one of key_mapping or prefix is provided
    _Validators._validate_mutually_exclusive_arguments(key_mapping, "key_mapping", prefix, "prefix")
    
    # Convert single Document to list
    docs = UtilFuncs._as_list(docs)
    
    if key_mapping:
        # Rename based on key_mapping
        for doc in docs:
            new_metadata = {}
            for key, value in doc.metadata.items():
                new_key = key_mapping.get(key, key)
                new_metadata[new_key] = value
            doc.metadata = new_metadata
    
    elif prefix:
        # Fetch reserved keywords from buffer or database
        reserved_keywords = _InternalBuffer.get("vs_reserved_keywords")
        if reserved_keywords is None:
            reserved_keywords = set(word.upper() for word in list_td_reserved_keywords())
            _InternalBuffer.add(vs_reserved_keywords=reserved_keywords)
        
        # Add prefix only to reserved keywords
        for doc in docs:
            new_metadata = {}
            for key, value in doc.metadata.items():
                if key.upper() in reserved_keywords:
                    new_key = f"{prefix}{key}"
                else:
                    new_key = key
                new_metadata[new_key] = value
            doc.metadata = new_metadata
    
    return docs