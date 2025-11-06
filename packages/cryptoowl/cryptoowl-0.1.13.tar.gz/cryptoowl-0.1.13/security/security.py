import json
import random
import time
from datetime import datetime

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# from common.secretmanager import SecretManager
from common_utils.time_utils import convert_timestamp_to_datetime
from db.databases import RDSConnection
from security.constants import HONEYPOT_FINDER_URL, GO_PLUS_URL, GET_QUICK_AUDIT_URL, QUICK_INTEL_API_KEY_SECRET_ID, \
    SOCIAL_INTELLIGENCE_DB_SECRET_ID, UPDATE_OTHER_CHAIN_SECURITY_DATA_QUERY
from common_utils.chain_utils import chain_to_id, id_to_chain

# Default timeout for all network requests (in seconds)
DEFAULT_TIMEOUT = 30

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds to wait between retries
RATE_LIMIT_STATUS = 429

write_db = RDSConnection(db_secret_name=SOCIAL_INTELLIGENCE_DB_SECRET_ID)

class Honeypot:
    def __init__(self, proxies=None):
        # self.__aws_secret_manager = SecretManager()
        # self.__api_key_values = self.__aws_secret_manager.get_secret_key_value(
        #     secret_name=QUICK_INTEL_API_KEY_SECRET_ID)
        # self.__api_key = self.__api_key_values.get("api-key")
        self.__session = requests.Session()
        self.__proxies = proxies
        
        # Log proxy information for debugging
        if self.__proxies:
            print(f"INFO: Honeypot initialized with {len(self.__proxies)} proxies")
        else:
            print("WARNING: Honeypot initialized with no proxies")

    @classmethod
    def __store_security_data(cls, security_data, verbose=False):
        if security_data:
            token_id = security_data.get("token_id")
            honeypot = security_data.get("honeypot")
            buy_tax = security_data.get("buy_tax")
            sell_tax = security_data.get("sell_tax")
            holder_count = security_data.get("holder_count")
            lp_burned = security_data.get("lp_burned")
            is_scam = security_data.get("is_scam")
            can_burn = security_data.get("can_burn")
            can_mint = security_data.get("can_mint")
            can_freeze = security_data.get("can_freeze")
            contract_creator = security_data.get("contract_creator")
            contract_owner = security_data.get("contract_owner")
            lp_lock_percentage = security_data.get("lp_lock_percentage")
            lp_unlock_date = security_data.get("lp_unlock_date")
            is_contract_verified = security_data.get("is_contract_verified")
            is_proxy = security_data.get("is_proxy")
            is_blacklisted = security_data.get("is_blacklisted")
            total_supply = security_data.get("total_supply")
            is_launchpad = security_data.get("is_launchpad")
            launchpad_name = security_data.get("launchpad_name")
            filled_by = security_data.get("filled_by") if security_data.get("filled_by") else "no_data"

            value = (honeypot, sell_tax, buy_tax, lp_burned, is_scam, can_burn, can_mint, can_freeze, holder_count,
                     contract_creator, contract_owner, lp_lock_percentage, lp_unlock_date, datetime.utcnow(),
                     filled_by, is_contract_verified, is_proxy, is_blacklisted, total_supply, is_launchpad, launchpad_name, token_id)
            query = UPDATE_OTHER_CHAIN_SECURITY_DATA_QUERY

            try:
                write_db.execute_query(query=query, values=value)
                if verbose:
                    print(f"INFO: Data updated for: {token_id}")
            except Exception as error:
                print(f"ERROR: {error}")

    def get_security_data(self, chain_id, token_id, should_update=True, verbose=False):
        # as of 19th february, we updated the logic of checking security data
        # first we check from quickintel ONLY if the chain is NOT supported by goplus
        # then we check from goplus if the chain is supported
        # if we got data from quickintel, we only add holder_count from goplus to that data,
        # but currently we are not calling quick intel for any go plus supported chain
        # else we use all data from goplus
        # and in any case for ethereum (1), bsc (56), and base (8453) we check from honeypot

        # Chains supported by GoPlus
        goplus_supported_chains = {1, 10, 25, 56, 100, 128, 137, 250, 321, 324, 10001, 201022, 42161, 43114, 59144,
            8453, "tron", 534352, 204, 5000, 42766, 81457, 169, 80085, 4200, 200901, 810180, 196}

        # Convert chain_id if it's a string
        if not isinstance(chain_id, int):
            chain_id = chain_to_id.get(chain_id)

        if not chain_id:
            return {"filled_by": "no_data", "error": f"Invalid or missing chain_id: {chain_id}. chain_id is required for this function.", "token_id": token_id, "chain": None, "chain_id": None}

        # Get chain name from id_to_chain map
        chain_name = id_to_chain.get(chain_id, str(chain_id))
        
        security_data_dict = None
        # Call quickintel **only if chain_id is NOT supported by GoPlus**
        # if chain_id not in goplus_supported_chains:
        #     if verbose:
        #         print('not supported by goplus')
        #     security_data_dict = self.get_data_from_quickintel(chain_id=chain_id, token_id=token_id)
        # else:
        #     security_data_dict = {"filled_by": "no_data"}

        # Fetch data from GoPlus for supported chains
        if chain_id in goplus_supported_chains:
            if verbose:
                print('fetching from goplus')
            security_data_dict = self.get_data_from_goplus(chain_id=chain_id, token_id=token_id,
                security_data=security_data_dict)

        # For Ethereum, BSC, and Base, check from honeypot
        if chain_id in (1, 56, 8453):
            security_data_dict = self.get_data_from_honeypot(chain_id=chain_id, token_id=token_id,
                security_data=security_data_dict)

        # Store data if required
        if should_update:
            self.__store_security_data(security_data=security_data_dict)

        # Ensure we always return a valid dictionary structure
        if not security_data_dict or not isinstance(security_data_dict, dict):
            security_data_dict = {"filled_by": "no_data"}
        
        # Ensure all expected fields exist with default values
        default_fields = {
            "token_id": token_id,
            "chain": chain_name,
            "chain_id": chain_id,
            "honeypot": None,
            "buy_tax": None,
            "sell_tax": None,
            "lp_burned": None,
            "is_scam": None,
            "can_burn": None,
            "can_mint": None,
            "can_freeze": None,
            "holders_count": None,
            "contract_creator": None,
            "contract_owner": None,
            "lp_lock_percentage": None,
            "lp_unlock_date": None,
            "is_contract_verified": None,
            "is_proxy": None,
            "is_blacklisted": None,
            "filled_by": security_data_dict.get("filled_by", "no_data")
        }
        
        # Merge with existing data, keeping existing values where available
        for key, default_value in default_fields.items():
            if key not in security_data_dict:
                security_data_dict[key] = default_value

        return security_data_dict

    @classmethod
    def _get_lp_locks_data_gp(cls, lp_lock_data):
        lp_lock_percentage = None
        if not lp_lock_data:
            return lp_lock_percentage

        for i in lp_lock_data:
            is_locked = i.get("is_locked")
            if is_locked:
                percentage_locked = float(i.get("percent")) if i.get("percent") else i.get("percent")
                if lp_lock_percentage is None:
                    lp_lock_percentage = percentage_locked
                else:
                    lp_lock_percentage += percentage_locked

        return lp_lock_percentage

    @classmethod
    def _get_lp_burned_data_gp(cls, lp_lock_data):
        """
        Calculate LP burned percentage from lp_holders array.
        LP is considered burned if it's sent to dead address (0xdead, 0x0000) and locked.
        """
        lp_burned_percentage = None
        if not lp_lock_data:
            return lp_burned_percentage

        burned_addresses = ["0x000000000000000000000000000000000000dead", "0x0000000000000000000000000000000000000000"]
        
        for holder in lp_lock_data:
            address = holder.get("address", "").lower()
            is_locked = holder.get("is_locked")
            
            # Check if address is a burned address and is locked
            if address in burned_addresses and is_locked:
                percent = holder.get("percent")
                if percent:
                    percent_float = float(percent)
                    if lp_burned_percentage is None:
                        lp_burned_percentage = percent_float
                    else:
                        lp_burned_percentage += percent_float

        return lp_burned_percentage

    def get_data_from_goplus(self, chain_id, token_id, security_data=None):
        if isinstance(chain_id, str):
            chain_id = chain_to_id.get(chain_id)

        if not chain_id:
            return {"filled_by": "no_data", "error": f"Invalid or missing chain_id: {chain_id}. chain_id is required for this function.", "token_id": token_id, "chain": None, "chain_id": None}

        # Get chain name from id_to_chain map
        chain_name = id_to_chain.get(chain_id, str(chain_id))

        token_id = token_id.lower()
        url = GO_PLUS_URL.format(chain_id=chain_id, token_id=token_id)
        retries = 0
        proxy = None  # Initialize proxy to None by default
        
        while retries <= MAX_RETRIES:
            try:
                # Handle proxy selection - use proxy if available, otherwise proceed without
                if self.__proxies and len(self.__proxies) > 0:
                    proxy = random.choice(self.__proxies)
                else:
                    proxy = None
                    print(f"WARNING: No proxies available for GoPlus request for token {token_id} - call will be made without proxy (risk of rate limiting)")

                response = self.__session.get(url=url, proxies=proxy, timeout=DEFAULT_TIMEOUT)
                if response.status_code == RATE_LIMIT_STATUS:
                    print(f"INFO: Rate limit hit for token {token_id}, retrying after {RETRY_DELAY} second")
                    time.sleep(RETRY_DELAY)
                    retries += 1
                    continue
                elif response.status_code == 200:
                    try:
                        result = response.json().get("result")
                        if result and token_id in result:
                            token_data = result.get(token_id)
                            if not token_data:
                                print(f"WARNING: No token data found in GoPlus response for {token_id}")
                                break
                            
                            buy_tax = token_data.get('buy_tax')
                            sell_tax = token_data.get('sell_tax')
                            is_honey_pot = token_data.get('is_honeypot')
                            can_mint = token_data.get('is_mintable')
                            is_proxy = token_data.get('is_proxy')
                            is_blacklisted = token_data.get('is_blacklisted')
                            is_contract_verified = token_data.get('is_open_source')
                            holders_count = token_data.get("holder_count")
                            contract_creator = token_data.get('creator_address')
                            contract_owner = token_data.get('owner_address')
                            lp_holders = token_data.get('lp_holders')
                            lp_lock_percentage = self._get_lp_locks_data_gp(lp_lock_data=lp_holders)
                            lp_burned_percentage = self._get_lp_burned_data_gp(lp_lock_data=lp_holders)
                            
                            # Extract new fields
                            total_supply = token_data.get('total_supply')
                            launchpad_token = token_data.get('launchpad_token', {})
                            is_launchpad = launchpad_token.get('is_launchpad_token')
                            launchpad_name = launchpad_token.get('launchpad_name')

                            # This block was designed for when QuickIntel was providing base security data
                            # GoPlus would only supplement with holder_count without overriding existing data
                            # This code won't be triggered anymore since QuickIntel is currently disabled
                            # (commented out in get_security_data method)
                            if security_data and security_data.get("filled_by") != "no_data":
                                security_data.update({
                                    "holder_count": holders_count,
                                })
                                return security_data

                            security_data_dict = {
                                "token_id": token_id,
                                "chain": chain_name,
                                "chain_id": chain_id,
                                "honeypot": int(is_honey_pot) if is_honey_pot else is_honey_pot,
                                "buy_tax": float(buy_tax) * 100 if buy_tax else buy_tax,
                                "sell_tax": float(sell_tax) * 100 if sell_tax else sell_tax,
                                "holder_count": int(holders_count) if holders_count else holders_count,
                                "can_mint": int(can_mint) if can_mint else can_mint,
                                "contract_creator": contract_creator,
                                "contract_owner": contract_owner,
                                "lp_lock_percentage": float(lp_lock_percentage) * 100 if lp_lock_percentage
                                else lp_lock_percentage,
                                "is_filled": True,
                                "is_proxy": int(is_proxy) if is_proxy else is_proxy,
                                "is_blacklisted": int(is_blacklisted) if is_blacklisted else is_blacklisted,
                                "is_contract_verified": int(is_contract_verified) if is_contract_verified
                                else is_contract_verified,
                                "filled_by": "goplus",
                                "total_supply": total_supply,
                                "is_launchpad": int(is_launchpad) if is_launchpad else is_launchpad,
                                "launchpad_name": launchpad_name,
                                "lp_burned": float(lp_burned_percentage) * 100 if lp_burned_percentage else lp_burned_percentage
                            }
                            return security_data_dict
                        else:
                            print(f"INFO: No results from GoPlus for token_id {token_id} | chain_id: {chain_id}")
                            break
                    except Exception as e:
                        print(f"ERROR: Failed to parse GoPlus response for token_id {token_id} | chain_id {chain_id}: {str(e)}")
                        break
                else:
                    print(f"ERROR: GoPlus API returned status {response.status_code}: {response.text}")
                    break
            except Timeout as e:
                print(f"ERROR: Request to GoPlus timed out for token {token_id} using proxy {proxy}: {str(e)}")
                retries += 1
            except ConnectionError as e:
                print(f"ERROR: Connection failed to GoPlus for token {token_id} using proxy {proxy}: {str(e)}")
                retries += 1
            except RequestException as e:
                print(f"ERROR: Request failed to GoPlus for token {token_id}: {str(e)}")
                break
            except Exception as e:
                print(f"ERROR: Unexpected error in get_data_from_goplus for token {token_id}: {str(e)}")
                break

        return {"filled_by": "no_data", "token_id": token_id, "chain": chain_name, "chain_id": chain_id}

    def get_data_from_honeypot(self, chain_id, token_id, security_data=None):
        # Convert chain_id to numeric if it's a string (v2 endpoint requires numeric chain_id)
        if not isinstance(chain_id, int):
            chain_id = chain_to_id.get(chain_id, chain_id)

        # Get chain name from id_to_chain map
        chain_name = id_to_chain.get(chain_id, str(chain_id))

        proxy = None  # Initialize proxy to None by default
        
        try:
            # Handle proxy selection - use proxy if available, otherwise proceed without
            if self.__proxies and len(self.__proxies) > 0:
                proxy = random.choice(self.__proxies)
            else:
                proxy = None
                print(f"WARNING: No proxies available for Honeypot request for token {token_id} - call will be made without proxy (risk of rate limiting)")

            url = HONEYPOT_FINDER_URL.format(token_id=token_id, chain_id=chain_id)
            response = self.__session.get(url=url, proxies=proxy, timeout=DEFAULT_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse new v2 API response format
                honeypot_result = data.get('honeypotResult', {})
                simulation_result = data.get('simulationResult', {})
                token_data = data.get('token', {})
                
                # Extract honeypot status
                is_honey_pot = honeypot_result.get('isHoneypot')
                
                # Extract tax information (convert to percentage if needed)
                buy_tax = simulation_result.get('buyTax')
                sell_tax = simulation_result.get('sellTax')
                
                # Round taxes if they are numeric
                if buy_tax is not None:
                    buy_tax = round(float(buy_tax))
                if sell_tax is not None:
                    sell_tax = round(float(sell_tax))
                
                # Extract additional fields from v2 API
                total_holders = token_data.get('totalHolders')
                is_open_source = data.get('contractCode', {}).get('openSource')

                security_data_dict = {
                    "token_id": token_id,
                    "chain": chain_name,
                    "chain_id": chain_id,
                    "honeypot": is_honey_pot,
                    "buy_tax": buy_tax,
                    "sell_tax": sell_tax,
                    "is_filled": True
                }
                
                # Add holder_count if available and not already set
                if total_holders and not (security_data and security_data.get("holder_count")):
                    security_data_dict["holder_count"] = int(total_holders)
                
                # Add additional fields if not already present in security_data
                if not security_data or not security_data.get("is_contract_verified"):
                    security_data_dict["is_contract_verified"] = int(is_open_source) if is_open_source is not None else None
                
                if security_data:
                    security_data.update(security_data_dict)
                    return security_data
                return security_data_dict
            else:
                print(f"ERROR: Honeypot API returned status {response.status_code} for token {token_id} on chain {chain_id}: {response.text}")
        except Timeout as e:
            print(f"ERROR: Request to Honeypot timed out for token {token_id} on chain {chain_id} using proxy {proxy}: {str(e)}")
        except ConnectionError as e:
            print(f"ERROR: Connection failed to Honeypot for token {token_id} on chain {chain_id} using proxy {proxy}: {str(e)}")
        except RequestException as e:
            print(f"ERROR: Request failed to Honeypot for token {token_id} on chain {chain_id} using proxy {proxy}: {str(e)}")
        except Exception as e:
            print(f"ERROR: Unexpected error in get_data_from_honeypot for token {token_id} on chain {chain_id} using proxy {proxy}: {str(e)}")

        # Return existing security_data if available (preserve GoPlus data), otherwise return no_data
        if security_data and security_data.get("filled_by") != "no_data":
            return security_data  # Keep existing GoPlus data
        else:
            return {"filled_by": "no_data", "token_id": token_id, "chain": chain_name, "chain_id": chain_id}

    @classmethod
    def _get_lp_locks_data_qi(cls, lp_lock_data):
        lp_lock_percentage = None
        lp_unlock_date = None
        if not lp_lock_data:
            return lp_lock_percentage, lp_unlock_date

        for key, value in lp_lock_data.items():
            if value and isinstance(value, dict):
                if percentage_locked := float(value.get("percentageLocked")) if value.get("percentageLocked") \
                                                                                and value.get("percentageLocked") != "NaN" \
                        else value.get("percentageLocked"):
                    if percentage_locked == "NaN":
                        continue
                    if lp_lock_percentage is None:
                        lp_lock_percentage = percentage_locked
                    else:
                        lp_lock_percentage += percentage_locked

                if unlock_date_timestamp := value.get("unlockDate"):
                    unlock_date = convert_timestamp_to_datetime(timestamp=unlock_date_timestamp)
                    if lp_unlock_date is None:
                        lp_unlock_date = unlock_date
                    else:
                        if lp_unlock_date > unlock_date:
                            lp_unlock_date = unlock_date

        return lp_lock_percentage, lp_unlock_date

    # def get_data_from_quickintel(self, chain_id, token_id):
    #     if isinstance(chain_id, int):
    #         chain_id = id_to_chain.get(chain_id)
    #
    #     if not chain_id:
    #         return {"filled_by": "no_data"}
    #
    #     url = GET_QUICK_AUDIT_URL
    #     payload = {"chain": chain_id, "tokenAddress": token_id}
    #     headers = {"X-QKNTL-KEY": self.__api_key, "Content-Type": "application/json"}
    #     retries = 0
    #
    #     while retries <= MAX_RETRIES:
    #         try:
    #             response = requests.post(url=url, data=json.dumps(payload), headers=headers, timeout=DEFAULT_TIMEOUT)
    #
    #             if response.status_code == RATE_LIMIT_STATUS:
    #                 print(f"INFO: Rate limit hit for token {token_id}, retrying after {RETRY_DELAY} second")
    #                 time.sleep(RETRY_DELAY)
    #                 retries += 1
    #                 continue
    #             elif response.status_code == 200:
    #                 data = response.json()
    #                 token_dynamic_details = data.get("tokenDynamicDetails") if data.get(
    #                     "tokenDynamicDetails") else {}
    #                 quick_audit = data.get("quickiAudit") if data.get("quickiAudit") else {}
    #
    #                 buy_tax = token_dynamic_details.get("buy_Tax")
    #                 sell_tax = token_dynamic_details.get("sell_Tax")
    #                 is_honey_pot = token_dynamic_details.get("is_Honeypot")
    #                 can_mint = quick_audit.get("can_Mint")
    #                 is_proxy = quick_audit.get("is_Proxy")
    #                 is_blacklisted = quick_audit.get("can_Blacklist")
    #                 is_contract_verified = data.get("contractVerified")
    #                 contract_creator = quick_audit.get("contract_Creator").lower() if quick_audit.get(
    #                     "contract_Creator") \
    #                     else quick_audit.get("contract_Creator")
    #                 contract_owner = quick_audit.get("contract_Owner").lower() if quick_audit.get("contract_Owner") \
    #                     else quick_audit.get("contract_Owner")
    #
    #                 lp_burned = token_dynamic_details.get("lp_Burned_Percent")
    #                 lp_lock = token_dynamic_details.get("lp_Locks")
    #                 lp_lock_percentage, lp_unlock_date = self._get_lp_locks_data_qi(lp_lock_data=lp_lock)
    #
    #                 is_scam = data.get("isScam")
    #                 can_burn = quick_audit.get("can_Burn")
    #                 can_freeze = quick_audit.get("can_Freeze_Trading")
    #
    #                 security_data_dict = {
    #                     "token_id": token_id,
    #                     "honeypot": is_honey_pot,
    #                     "buy_tax": buy_tax,
    #                     "sell_tax": sell_tax,
    #                     "lp_burned": lp_burned,
    #                     "is_scam": is_scam,
    #                     "can_burn": can_burn,
    #                     "can_mint": can_mint,
    #                     "can_freeze": can_freeze,
    #                     "contract_creator": contract_creator,
    #                     "contract_owner": contract_owner,
    #                     "lp_lock_percentage": float(
    #                         lp_lock_percentage) if lp_lock_percentage else lp_lock_percentage,
    #                     "lp_unlock_date": lp_unlock_date,
    #                     "is_contract_verified": is_contract_verified,
    #                     "is_filled": True,
    #                     "is_proxy": is_proxy,
    #                     "is_blacklisted": is_blacklisted,
    #                     "filled_by": "quick_intel"
    #                 }
    #                 return security_data_dict
    #             else:
    #                 print(f"ERROR: QuickIntel API returned status {response.status_code}: {response.text}")
    #                 break
    #         except Timeout:
    #             print(f"ERROR: Request to QuickIntel timed out for token {token_id}")
    #             retries += 1
    #         except ConnectionError:
    #             print(f"ERROR: Connection failed to QuickIntel for token {token_id}")
    #             retries += 1
    #         except RequestException as e:
    #             print(f"ERROR: Request failed to QuickIntel for token {token_id}: {str(e)}")
    #             break
    #         except Exception as e:
    #             print(f"ERROR: Unexpected error in get_data_from_quickintel for token {token_id}: {str(e)}")
    #             break
    #
    #     return {"filled_by": "no_data", "chain": chain_id, "chain_id": chain_id}
