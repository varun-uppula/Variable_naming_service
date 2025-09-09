from app.services.naming_service import NamingService

# Instantiate the NamingService class, with 'internal' as the standard
namer = NamingService()

# Manually add fake entry to simulate wrong-but-present abbreviation (if needed)

# Test with a custom description and specific standard
result = namer.generate_variable_name(
    module="Balance Control", 
    data_type="Global variable, volatile memory", 
    data_size="Array/vector",
    unit="Binary (true/false)", 
    description="this is related to battery management system", 
    standard="autosar"
)

# Print the result of the generated variable name
print(result)
