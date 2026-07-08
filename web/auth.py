#!/usr/bin/env python3
"""
FreeIPA/LDAP Authentication Module for LRN_PXE

Provides LDAP authentication, group membership checks, and user info retrieval
for integration with FreeIPA identity management systems.
"""

import ldap
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class FreeIPAAuth:
    """FreeIPA/LDAP authentication handler."""
    
    def __init__(
        self,
        server: str,
        base_dn: str,
        admin_group: str = "lrn-pxe-admins",
        timeout: int = 10
    ):
        """
        Initialize FreeIPA authentication.
        
        Args:
            server: LDAP server hostname/IP (e.g., "ipa.example.com")
            base_dn: Base distinguished name (e.g., "dc=example,dc=com")
            admin_group: FreeIPA group for admins (default: "lrn-pxe-admins")
            timeout: LDAP connection timeout in seconds (default: 10)
        """
        self.server = server
        self.base_dn = base_dn
        self.admin_group = admin_group
        self.timeout = timeout
        self.users_dn = f"cn=users,cn=accounts,{base_dn}"
        self.groups_dn = f"cn=groups,cn=accounts,{base_dn}"
        
    def _get_connection(self, bind_dn: Optional[str] = None, password: Optional[str] = None):
        """
        Establish LDAP connection.
        
        Args:
            bind_dn: DN to bind as (None for anonymous)
            password: Password for bind (None for anonymous)
            
        Returns:
            LDAP connection object
            
        Raises:
            ldap.LDAPError: Connection or binding failed
        """
        try:
            conn = ldap.initialize(f"ldap://{self.server}")
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT, self.timeout)
            
            if bind_dn and password:
                conn.simple_bind_s(bind_dn, password)
                logger.debug(f"LDAP bind successful for {bind_dn}")
            else:
                conn.simple_bind_s()
                logger.debug("LDAP anonymous bind successful")
                
            return conn
        except ldap.LDAPError as e:
            logger.error(f"LDAP connection error: {e}")
            raise
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user with username and password.
        
        Args:
            username: FreeIPA username
            password: User password
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            user_dn = f"uid={username},cn=users,cn=accounts,{self.base_dn}"
            conn = self._get_connection(user_dn, password)
            conn.unbind_s()
            logger.info(f"Authentication successful for user: {username}")
            return True
            
        except ldap.INVALID_CREDENTIALS:
            logger.warning(f"Authentication failed for user: {username}")
            return False
        except ldap.LDAPError as e:
            logger.error(f"LDAP error during authentication for {username}: {e}")
            return False
    
    def get_user_info(self, username: str, admin_dn: str, admin_password: str) -> Optional[Dict]:
        """
        Get user information from FreeIPA.
        
        Args:
            username: FreeIPA username
            admin_dn: Administrator DN for querying (e.g., uid=admin,cn=users,cn=accounts,...)
            admin_password: Administrator password
            
        Returns:
            Dictionary with user info (uid, mail, displayName, memberOf) or None if not found
        """
        try:
            conn = self._get_connection(admin_dn, admin_password)
            
            result = conn.search_s(
                self.users_dn,
                ldap.SCOPE_SUBTREE,
                f"(uid={username})",
                ['uid', 'mail', 'displayName', 'memberOf']
            )
            
            if result:
                dn, attrs = result[0]
                # Convert byte strings to regular strings
                user_info = {
                    'dn': dn,
                    'uid': attrs.get(b'uid', [b''])[0].decode() if b'uid' in attrs else username,
                    'mail': attrs.get(b'mail', [b''])[0].decode() if b'mail' in attrs else '',
                    'displayName': attrs.get(b'displayName', [b''])[0].decode() if b'displayName' in attrs else username,
                    'memberOf': [m.decode() for m in attrs.get(b'memberOf', [])]
                }
                logger.debug(f"Retrieved info for user: {username}")
                return user_info
            else:
                logger.warning(f"User not found in LDAP: {username}")
                return None
                
        except ldap.LDAPError as e:
            logger.error(f"LDAP error retrieving user info for {username}: {e}")
            return None
    
    def is_admin(self, username: str, admin_dn: str, admin_password: str) -> bool:
        """
        Check if user is member of admin group.
        
        Args:
            username: FreeIPA username
            admin_dn: Administrator DN for querying
            admin_password: Administrator password
            
        Returns:
            True if user is admin group member, False otherwise
        """
        try:
            user_info = self.get_user_info(username, admin_dn, admin_password)
            if not user_info:
                return False
            
            groups = [dn.split(',')[0].split('=')[1] for dn in user_info.get('memberOf', [])]
            is_admin = self.admin_group in groups
            
            if is_admin:
                logger.info(f"User {username} verified as admin")
            else:
                logger.debug(f"User {username} is not admin")
                
            return is_admin
            
        except Exception as e:
            logger.error(f"Error checking admin status for {username}: {e}")
            return False
    
    def get_user_groups(self, username: str, admin_dn: str, admin_password: str) -> List[str]:
        """
        Get all groups user belongs to.
        
        Args:
            username: FreeIPA username
            admin_dn: Administrator DN for querying
            admin_password: Administrator password
            
        Returns:
            List of group names
        """
        try:
            user_info = self.get_user_info(username, admin_dn, admin_password)
            if not user_info:
                return []
            
            groups = [dn.split(',')[0].split('=')[1] for dn in user_info.get('memberOf', [])]
            logger.debug(f"User {username} groups: {groups}")
            return groups
            
        except Exception as e:
            logger.error(f"Error retrieving groups for {username}: {e}")
            return []
    
    def group_exists(self, group_name: str, admin_dn: str, admin_password: str) -> bool:
        """
        Check if a group exists in FreeIPA.
        
        Args:
            group_name: Group name (cn)
            admin_dn: Administrator DN
            admin_password: Administrator password
            
        Returns:
            True if group exists, False otherwise
        """
        try:
            conn = self._get_connection(admin_dn, admin_password)
            
            result = conn.search_s(
                self.groups_dn,
                ldap.SCOPE_SUBTREE,
                f"(cn={group_name})"
            )
            
            exists = bool(result)
            logger.debug(f"Group {group_name} exists: {exists}")
            return exists
            
        except ldap.LDAPError as e:
            logger.error(f"LDAP error checking group {group_name}: {e}")
            return False


def create_auth_from_settings(settings: Dict) -> Optional[FreeIPAAuth]:
    """
    Create FreeIPAAuth instance from settings dictionary.
    
    Args:
        settings: Dictionary with keys:
            - ldap_server: LDAP server hostname
            - ldap_base_dn: Base DN
            - ldap_admin_group: Admin group name (optional, default: lrn-pxe-admins)
            
    Returns:
        FreeIPAAuth instance or None if required settings missing
    """
    required_keys = ['ldap_server', 'ldap_base_dn']
    
    if not all(k in settings for k in required_keys):
        logger.error("Missing required LDAP settings")
        return None
    
    return FreeIPAAuth(
        server=settings['ldap_server'],
        base_dn=settings['ldap_base_dn'],
        admin_group=settings.get('ldap_admin_group', 'lrn-pxe-admins')
    )
