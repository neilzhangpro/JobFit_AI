"""Unit of Work interface — defines the transactional boundary for write operations.

Application services use this interface to ensure all repository operations
within a use case are committed or rolled back together.
"""

# TODO(#20): Define IUnitOfWork ABC with commit(), rollback(), __aenter__, __aexit__
