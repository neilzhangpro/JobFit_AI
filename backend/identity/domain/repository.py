"""IUserRepository and ITenantRepository interfaces (ABC).

Repository interfaces define the contract for data access.
Implementations should be in the infrastructure layer.
"""

# TODO: Implement IUserRepository abstract base class
#   - Methods: find_by_id, find_by_email, find_by_tenant_id, save, delete
#   - All methods must include tenant_id parameter for multi-tenant isolation
#   - Use ABC and abstractmethod decorators

# TODO: Implement ITenantRepository abstract base class
#   - Methods: find_by_id, find_by_name, save, delete
#   - Include tenant_id parameter where applicable
#   - Use ABC and abstractmethod decorators
