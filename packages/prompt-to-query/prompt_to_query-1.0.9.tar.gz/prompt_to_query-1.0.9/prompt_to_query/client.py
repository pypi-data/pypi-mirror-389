import ctypes
import json
import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional


class PromptToQueryError(Exception):
    """Base exception for PromptToQuery SDK errors"""
    pass


class PromptToQuery:
    """
    Main SDK client for converting prompts to MongoDB queries

    Example:
        >>> ptq = PromptToQuery(
        ...     llm_provider="openai",
        ...     api_key="sk-...",
        ...     db_schema_path="schema.json"
        ... )
        >>> query = ptq.generate_query("Get all active users")
        >>> print(query)
        {'operation': 'find', 'collection': 'users', 'filter': {'status': 'active'}}
    """

    def __init__(
        self,
        llm_provider: str,
        api_key: str,
        db_schema: Optional[Dict[str, Any]] = None,
        db_schema_path: Optional[str] = None,
        model: Optional[str] = None,
        lib_path: Optional[str] = None
    ):
        """
        Initialize the PromptToQuery client

        Args:
            llm_provider: LLM provider to use ("openai" or "anthropic")
            api_key: API key for the LLM provider
            db_schema: Database schema as a dictionary
            db_schema_path: Path to JSON file containing database schema
            model: Specific model to use (optional, uses defaults if not provided)
            lib_path: Custom path to the shared library (optional)

        Raises:
            PromptToQueryError: If initialization fails
            ValueError: If neither db_schema nor db_schema_path is provided
        """
        if db_schema is None and db_schema_path is None:
            raise ValueError("Either db_schema or db_schema_path must be provided")

        # Load schema from file if path is provided
        if db_schema_path:
            with open(db_schema_path, 'r') as f:
                db_schema = json.load(f)

        # Load the shared library
        self._lib = self._load_library(lib_path)

        # Define function signatures
        self._define_functions()

        # Initialize the SDK
        config = {
            "llm_provider": llm_provider,
            "api_key": api_key,
            "db_schema": json.dumps(db_schema),
        }

        if model:
            config["model"] = model

        config_json = json.dumps(config)
        result = self._lib.InitSDK(config_json.encode('utf-8'))
        result_str = ctypes.c_char_p(result).value.decode('utf-8')
        result_data = json.loads(result_str)

        if "error" in result_data:
            raise PromptToQueryError(f"Initialization failed: {result_data['error']}")

    def _load_library(self, custom_path: Optional[str] = None) -> ctypes.CDLL:
        """Load the shared library based on the platform"""
        if custom_path:
            return ctypes.CDLL(custom_path)

        # Determine library name based on platform
        system = platform.system()
        machine = platform.machine()

        # Determine the library name with platform and architecture
        lib_name = self._get_library_name(system, machine)

        # Try multiple search paths
        search_paths = self._get_search_paths()

        for search_dir in search_paths:
            lib_path = search_dir / lib_name
            if lib_path.exists():
                return ctypes.CDLL(str(lib_path))

        # If not found with specific name, try fallback names
        fallback_names = self._get_fallback_names(system)
        for search_dir in search_paths:
            for fallback_name in fallback_names:
                lib_path = search_dir / fallback_name
                if lib_path.exists():
                    return ctypes.CDLL(str(lib_path))

        # Library not found
        raise PromptToQueryError(
            f"Library not found for {system} {machine}. "
            f"Searched in: {', '.join(str(p) for p in search_paths)}. "
            f"Looking for: {lib_name}. "
            "Please build the project first or install the pre-built package."
        )

    def _get_library_name(self, system: str, machine: str) -> str:
        """Get the expected library name for the platform"""
        if system == "Linux":
            # Check if we're running on Alpine (musl) or standard Linux (glibc)
            is_musl = self._is_musl_libc()
            if machine in ["x86_64", "AMD64"]:
                return "libprompttoquery_linux_amd64_musl.so" if is_musl else "libprompttoquery_linux_amd64.so"
            elif machine in ["aarch64", "arm64"]:
                return "libprompttoquery_linux_arm64_musl.so" if is_musl else "libprompttoquery_linux_arm64.so"
            else:
                return "libprompttoquery.so"

        elif system == "Darwin":  # macOS
            if machine in ["x86_64", "AMD64"]:
                return "libprompttoquery_darwin_amd64.dylib"
            elif machine == "arm64":
                return "libprompttoquery_darwin_arm64.dylib"
            else:
                return "libprompttoquery.dylib"

        elif system == "Windows":
            if machine in ["x86_64", "AMD64"]:
                return "prompttoquery_windows_amd64.dll"
            elif machine in ["aarch64", "arm64"]:
                return "prompttoquery_windows_arm64.dll"
            else:
                return "prompttoquery.dll"

        else:
            raise PromptToQueryError(f"Unsupported platform: {system}")

    def _get_search_paths(self) -> list:
        """Get list of directories to search for the library"""
        paths = []

        # 1. First check the package's lib directory (for installed package)
        package_dir = Path(__file__).parent
        lib_dir = package_dir / "lib"
        if lib_dir.exists():
            paths.append(lib_dir)

        # 2. Check the build directory (for development)
        sdk_dir = package_dir.parent.parent.parent
        build_dir = sdk_dir / "core" / "build"
        if build_dir.exists():
            paths.append(build_dir)

        # 3. Check current directory
        paths.append(Path.cwd())

        return paths

    def _get_fallback_names(self, system: str) -> list:
        """Get fallback library names for the platform"""
        fallback_names = []

        if system == "Linux":
            # Try musl variant if glibc was expected, and vice versa
            fallback_names.extend([
                "libprompttoquery_linux_amd64.so",
                "libprompttoquery_linux_amd64_musl.so",
                "libprompttoquery_linux_arm64.so",
                "libprompttoquery_linux_arm64_musl.so",
                "libprompttoquery.so"
            ])
        elif system == "Darwin":
            fallback_names.extend([
                "libprompttoquery_darwin_amd64.dylib",
                "libprompttoquery_darwin_arm64.dylib",
                "libprompttoquery.dylib"
            ])
        elif system == "Windows":
            fallback_names.extend([
                "prompttoquery_windows_amd64.dll",
                "prompttoquery.dll"
            ])

        return fallback_names

    def _is_musl_libc(self) -> bool:
        """Check if the system is using musl libc (Alpine Linux)"""
        try:
            # Check for musl in ldd output
            result = os.popen("ldd --version 2>&1").read()
            return "musl" in result.lower()
        except:
            return False

    def _define_functions(self):
        """Define the C function signatures"""
        # InitSDK(configJSON *C.char) *C.char
        self._lib.InitSDK.argtypes = [ctypes.c_char_p]
        self._lib.InitSDK.restype = ctypes.c_char_p

        # GenerateQuery(prompt *C.char) *C.char
        self._lib.GenerateQuery.argtypes = [ctypes.c_char_p]
        self._lib.GenerateQuery.restype = ctypes.c_char_p

        # ExplainQuery(queryJSON *C.char) *C.char
        self._lib.ExplainQuery.argtypes = [ctypes.c_char_p]
        self._lib.ExplainQuery.restype = ctypes.c_char_p

        # SuggestDatabaseImprovements(queryJSON *C.char) *C.char
        self._lib.SuggestDatabaseImprovements.argtypes = [ctypes.c_char_p]
        self._lib.SuggestDatabaseImprovements.restype = ctypes.c_char_p

        # ImprovePrompt(queryJSON *C.char, originalPrompt *C.char) *C.char
        self._lib.ImprovePrompt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.ImprovePrompt.restype = ctypes.c_char_p

        # GetVersion() *C.char
        self._lib.GetVersion.argtypes = []
        self._lib.GetVersion.restype = ctypes.c_char_p

    def generate_query(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a MongoDB query from a natural language prompt

        Args:
            prompt: Natural language description of the desired query

        Returns:
            Dictionary containing:
            - query: MongoDB query object with keys like:
                - operation: "find", "aggregate", or "count"
                - collection: Name of the collection
                - filter: Query filter (for find/count)
                - pipeline: Aggregation pipeline (for aggregate)
                - projection, sort, limit, skip: Optional parameters
            - columnTitles: Array of human-readable column titles for the returned data

        Raises:
            PromptToQueryError: If query generation fails

        Example:
            >>> result = ptq.generate_query("Get top 10 products by price")
            >>> print(result['query'])
            {'operation': 'find', 'collection': 'products', 'sort': {'price': -1}, 'limit': 10}
            >>> print(result['columnTitles'])
            ['Product Name', 'Price', 'Category', 'Stock']
        """
        result = self._lib.GenerateQuery(prompt.encode('utf-8'))
        result_str = ctypes.c_char_p(result).value.decode('utf-8')
        result_data = json.loads(result_str)

        if "error" in result_data:
            raise PromptToQueryError(f"Query generation failed: {result_data['error']}")

        # Parse the query JSON string
        query = json.loads(result_data["query"])
        column_titles = result_data.get("columnTitles", [])

        return {
            "query": query,
            "columnTitles": column_titles
        }

    def explain_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explain what a MongoDB query does in natural language

        Args:
            query: MongoDB query object (from generate_query result)

        Returns:
            Dictionary containing:
            - explanation: Complete natural language explanation of what the query does
            - operation: Type of operation ("find", "aggregate", or "count")
            - targetCollection: Collection being queried
            - dataReturned: List of fields/data that will be returned
            - filters: List of filter descriptions in plain language
            - sorting: Sort description (if applicable)
            - limitations: Limit/skip description (if applicable)
            - complexity: Query complexity ("low", "medium", or "high")
            - estimatedDocuments: Estimated number of documents

        Raises:
            PromptToQueryError: If explanation fails

        Example:
            >>> result = ptq.generate_query("Get top 10 products by price")
            >>> explanation = ptq.explain_query(result['query'])
            >>> print(explanation['explanation'])
            'This query retrieves the top 10 products sorted by price in descending order'
            >>> print(explanation['operation'])
            'find'
            >>> print(explanation['complexity'])
            'low'
        """
        query_json = json.dumps(query)
        result = self._lib.ExplainQuery(query_json.encode('utf-8'))
        result_str = ctypes.c_char_p(result).value.decode('utf-8')
        result_data = json.loads(result_str)

        if "error" in result_data:
            raise PromptToQueryError(f"Query explanation failed: {result_data['error']}")

        return {
            "explanation": result_data.get("explanation", ""),
            "operation": result_data.get("operation", ""),
            "targetCollection": result_data.get("targetCollection", ""),
            "dataReturned": result_data.get("dataReturned", []),
            "filters": result_data.get("filters", []),
            "sorting": result_data.get("sorting", ""),
            "limitations": result_data.get("limitations", ""),
            "complexity": result_data.get("complexity", "medium"),
            "estimatedDocuments": result_data.get("estimatedDocuments", "unknown")
        }

    def suggest_database_improvements(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get database optimization suggestions for a query

        Args:
            query: MongoDB query object (from generate_query result)

        Returns:
            Dictionary containing:
            - indexRecommendations: List of specific index recommendations with MongoDB commands
            - performanceHints: List of performance optimization hints
            - schemaOptimizations: List of schema design suggestions
            - queryOptimization: Alternative query approach description
            - estimatedImprovement: Expected performance gain
            - priority: Priority level ("high", "medium", or "low")

        Raises:
            PromptToQueryError: If analysis fails

        Example:
            >>> result = ptq.generate_query("Get top 10 products by price")
            >>> improvements = ptq.suggest_database_improvements(result['query'])
            >>> print(improvements['indexRecommendations'])
            [{'collection': 'products', 'fields': ['price'], 'type': 'single', ...}]
            >>> print(improvements['estimatedImprovement'])
            '10-100x faster for sort operations'
        """
        query_json = json.dumps(query)
        result = self._lib.SuggestDatabaseImprovements(query_json.encode('utf-8'))
        result_str = ctypes.c_char_p(result).value.decode('utf-8')
        result_data = json.loads(result_str)

        if "error" in result_data:
            raise PromptToQueryError(f"Database improvement suggestion failed: {result_data['error']}")

        return {
            "indexRecommendations": result_data.get("indexRecommendations", []),
            "performanceHints": result_data.get("performanceHints", []),
            "schemaOptimizations": result_data.get("schemaOptimizations", []),
            "queryOptimization": result_data.get("queryOptimization", ""),
            "estimatedImprovement": result_data.get("estimatedImprovement", ""),
            "priority": result_data.get("priority", "medium")
        }

    def improve_prompt(self, query: Dict[str, Any], original_prompt: str) -> Dict[str, Any]:
        """
        Get suggestions to improve the natural language prompt

        Args:
            query: MongoDB query object (from generate_query result)
            original_prompt: The original natural language prompt

        Returns:
            Dictionary containing:
            - originalPrompt: The user's original prompt
            - improvedPrompt: Suggested improved version of the prompt
            - ambiguities: List of detected ambiguities
            - missingDetails: List of details that could be added
            - suggestions: List of specific improvement suggestions
            - clarityScore: Clarity assessment ("excellent", "good", "fair", or "poor")
            - availableFields: List of relevant fields from the schema
            - examplePrompts: List of example well-written prompts

        Raises:
            PromptToQueryError: If analysis fails

        Example:
            >>> result = ptq.generate_query("Get products")
            >>> improvement = ptq.improve_prompt(result['query'], "Get products")
            >>> print(improvement['improvedPrompt'])
            'Get all active products sorted by price in descending order, limited to 10 results'
            >>> print(improvement['clarityScore'])
            'poor'
            >>> print(improvement['suggestions'])
            ['Add sort order', 'Specify filters', 'Add limit']
        """
        query_json = json.dumps(query)
        result = self._lib.ImprovePrompt(query_json.encode('utf-8'), original_prompt.encode('utf-8'))
        result_str = ctypes.c_char_p(result).value.decode('utf-8')
        result_data = json.loads(result_str)

        if "error" in result_data:
            raise PromptToQueryError(f"Prompt improvement failed: {result_data['error']}")

        return {
            "originalPrompt": result_data.get("originalPrompt", original_prompt),
            "improvedPrompt": result_data.get("improvedPrompt", ""),
            "ambiguities": result_data.get("ambiguities", []),
            "missingDetails": result_data.get("missingDetails", []),
            "suggestions": result_data.get("suggestions", []),
            "clarityScore": result_data.get("clarityScore", "fair"),
            "availableFields": result_data.get("availableFields", []),
            "examplePrompts": result_data.get("examplePrompts", [])
        }

    def get_version(self) -> str:
        """Get the SDK version"""
        result = self._lib.GetVersion()
        return ctypes.c_char_p(result).value.decode('utf-8')

    def __repr__(self) -> str:
        return f"<PromptToQuery version={self.get_version()}>"
