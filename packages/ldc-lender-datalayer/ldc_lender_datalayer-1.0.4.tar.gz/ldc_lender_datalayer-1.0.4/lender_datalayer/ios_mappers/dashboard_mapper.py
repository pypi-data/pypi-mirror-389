"""
Dashboard Mapper using BaseDataLayer architecture
Converts the old dashboard_mapper.py to use the new data layer pattern
"""

from ..ims_mappers.investor_mapper import InvestorMapper
from ..base_datalayer import BaseDataLayer
from ..common.constants import AddBankAccountConstant, ApplicationConfigDashboardConstant, InvestorSource, ProductConstants,\
    ProductFormConstants, FMPPDatabaseLink, ReferenceConstant, UserGroup
from django.conf import settings


class DashboardMapper(BaseDataLayer):
    """
    Dashboard Mapper using BaseDataLayer for database operations
    Handles dashboard configuration and user management operations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_DASHBOARD"

    @staticmethod
    def get_dashboard_config_keys(logical_reference):
        query = """
            SELECT config_type, config_key
            FROM lendenapp_application_config
        """

        params = {}
        if "ALL" not in logical_reference:
            query += f"WHERE logical_reference = ANY(%s) "
            params = [logical_reference]

        query += """
            GROUP BY config_type, config_key
            ORDER BY config_type, config_key
        """

        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_all_form_configuration(logical_reference):
        refs = logical_reference or []
        required_logical_reference = [
            ProductFormConstants.PRODUCT_FORM,
            ProductFormConstants.FORM,
        ]
        has_all = "ALL" in refs
        has_required_subset = all(
            form_reference in refs for form_reference in required_logical_reference
        )

        if not has_all and not has_required_subset:
            return []

        query = """
          SELECT config_type, config_key
          FROM lendenapp_application_config
          WHERE form_configuration IS NOT NULL or logical_reference=%(logical_reference)s
        """
        params = {"logical_reference": ProductFormConstants.PRODUCT_FORM}

        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_config_value_form_configuration(config_type, config_key):
        query = """
         SELECT config_value,form_configuration
         FROM lendenapp_application_config
         WHERE config_type = %s AND config_key = %s and form_configuration is not null
        """
        params = [config_type, config_key]
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    def get_dashboard_users(self, allowed_roles):
        query = """
            SELECT 
            lc.first_name as name,
            lc.email,
            lc.id,
            array_agg(ag.name) as roles
            FROM
                lendenapp_customuser lc
            JOIN
                lendenapp_customuser_groups lcg ON lc.id = lcg.customuser_id
            JOIN
                auth_group ag ON ag.id = lcg.group_id
            WHERE
                ag.name = ANY(%(allowed_roles)s)
            GROUP BY
                lc.id;
        """

        params = {"allowed_roles": allowed_roles}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def delete_user_role(self, user_pk, role):
        query = """
            DELETE FROM lendenapp_customuser_groups
            WHERE customuser_id = %(user_pk)s
            AND group_id = (SELECT id FROM auth_group WHERE name = %(role)s) RETURNING 1
        """
        params = {"user_pk": user_pk, "role": role}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def search_user(self, search_term):
        query = """
            SELECT 
            lc.first_name as name,
            lc.email,
            lc.id,
            array_agg(ag.name) as roles
            FROM
                lendenapp_customuser lc
            LEFT JOIN
                lendenapp_customuser_groups lcg ON lc.id = lcg.customuser_id
            LEFT JOIN
                auth_group ag ON ag.id = lcg.group_id
            WHERE
                lc.email = %(search_term)s
            GROUP BY lc.id;
        """
        params = {"search_term": search_term}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def get_roles(self, user_id):
        query = """
            SELECT ag.name
            FROM auth_group ag
            JOIN lendenapp_customuser_groups lcg ON ag.id = lcg.group_id
            WHERE lcg.customuser_id = %(user_id)s
        """
        params = {"user_id": user_id}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def assign_role(self, user_id, role_name):
        query = """
            INSERT INTO lendenapp_customuser_groups (customuser_id, group_id)
            VALUES (%(user_id)s, (SELECT id FROM auth_group WHERE name = %(role_name)s))
            RETURNING 1
        """
        params = {"user_id": user_id, "role_name": role_name}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_dashboard_data(query):
        return DashboardMapper().sql_execute_fetch_all(query, [], to_dict=True)
    
    @staticmethod
    def daily_transaction_details(transaction_type, start_date, end_date):
        status_list = [
            ApplicationConfigDashboardConstant.ANALYTICS_CONSTANT['SUCCESS'],
            ApplicationConfigDashboardConstant.ANALYTICS_CONSTANT['FAILED'],
            ApplicationConfigDashboardConstant.ANALYTICS_CONSTANT['PROCESSING']
        ]
        # return zero if no data
        query = """
        SELECT count(*), status 
        FROM lendenapp_transaction lt 
        WHERE type = %(transaction_type)s
        AND date >= %(start_date)s
        AND date < %(end_date)s
        AND status = ANY(%(status_list)s) 
        GROUP BY status
        """
        params = {'transaction_type': transaction_type, 'start_date': start_date, 'end_date': end_date, 'status_list': status_list}
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

        # In your dashboard_mapper.py file

    @staticmethod
    def funnel_data(start_date, end_date):
        query = """
        SELECT 
        DATE(lendenapp_timeline.created_date) AS activity_date,
        COUNT(DISTINCT CASE WHEN lendenapp_timeline.activity = 'SIGN_UP' THEN lendenapp_timeline.user_source_group_id END) AS SIGN_UP,
        COUNT(DISTINCT CASE WHEN lendenapp_timeline.activity = 'VERIFY_IDENTITY' THEN lendenapp_timeline.user_source_group_id END) AS VERIFY_IDENTITY,
        COUNT(DISTINCT CASE WHEN lendenapp_timeline.activity = 'LIVE_KYC' THEN lendenapp_timeline.user_source_group_id END) AS LIVE_KYC,
        COUNT(DISTINCT CASE WHEN lendenapp_timeline.activity = 'LEGAL_AUTHORIZATION' THEN lendenapp_timeline.user_source_group_id END) AS LEGAL_AUTHORIZATION,
        COUNT(DISTINCT CASE WHEN lendenapp_timeline.activity = 'BANK_ACCOUNT' THEN lendenapp_timeline.user_source_group_id END) AS BANK_ACCOUNT,
        COUNT(DISTINCT CASE WHEN lendenapp_timeline.activity = 'CONSENT AGREED' AND la.status = 'LISTED' THEN lendenapp_timeline.user_source_group_id END) AS LISTED,
        COUNT(DISTINCT CASE WHEN lendenapp_timeline.activity = 'CONSENT AGREED' AND la.status = 'OPEN' THEN lendenapp_timeline.user_source_group_id END) AS OPEN
        FROM lendenapp_timeline
        JOIN lendenapp_user_source_group lusg ON lusg.id = lendenapp_timeline.user_source_group_id
        LEFT JOIN lendenapp_account la ON la.user_source_group_id = lusg.id 
        WHERE lusg.source_id = 7 
        AND lendenapp_timeline.created_date >= %(start_date)s
        AND lendenapp_timeline.created_date <= %(end_date)s
        GROUP BY DATE(lendenapp_timeline.created_date)
        ORDER BY DATE(lendenapp_timeline.created_date) DESC"""

        params = {'start_date': start_date, 'end_date': end_date}
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def kyc_failure_count(start_date, end_date):
        query="""
        SELECT
        luk.event_code,luk.service_type,
        COUNT(DISTINCT luk.id) AS failure_count
        FROM
            lendenapp_userkyctracker AS lukt 
        INNER JOIN
            lendenapp_userkyc AS luk ON luk.tracking_id = lukt.tracking_id
        WHERE
            lukt.kyc_type = 'LIVE KYC'
            AND lukt.kyc_source = 'KMI'
            AND lukt.created_date >= %(start_date)s
            AND lukt.created_date <= %(end_date)s
            AND lukt.status = 'FAILED'
        GROUP BY
            luk.event_code,luk.service_type
        ORDER BY
            failure_count DESC; """

        params = {'start_date': start_date, 'end_date': end_date}
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)


    @staticmethod
    def get_lending_summary_dashboard(from_date, to_date):
        fmpp_database_link = FMPPDatabaseLink.PRODUCTION \
            if settings.SERVER_TYPE == 'PRODUCTION' else FMPPDatabaseLink.DEVELOPMENT

        query = f"""
            SELECT 
            CASE 
                WHEN tmp.value_1 = 'LDC' THEN {ProductConstants.LDCProduct} 
                ELSE {ProductConstants.CPProduct}
            END AS partner_code,
            sum(investment_amount)
            FROM {fmpp_database_link}.t_investor_scheme tis
            INNER JOIN {fmpp_database_link}.t_mst_parameter tmp 
            ON tis.partner_code_id = tmp.id
            WHERE tis.created_date
        """

        if from_date and to_date:
            query += " BETWEEN %(from_date)s AND %(to_date)s"
            params = {'from_date': from_date, 'to_date': to_date}
        else:
            todays_date =get_todays_date()
            query += " = %(todays_date)s"
            params = {'todays_date': todays_date}

        query += " GROUP BY partner_code"

        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_pending_supply_tenure_wise(start_date, end_date):
        query = f"""
            SELECT
                CASE
                    WHEN ls2.source_name = ANY(ARRAY['{InvestorSource.LCP}', '{InvestorSource.MCP}']) THEN 'CP'
                    WHEN ls2.source_name = ANY(ARRAY['{InvestorSource.LDC}']) THEN 'Retail'
                END as source_name,
                lendenapp_transaction."date"::date as "Date",
                SUM(ls.amount) as "Total_supply",
                SUM(CASE WHEN ls.status IN ('SUCCESS') THEN ls.amount ELSE 0 END) as "Available_supply_deployed",
                SUM(CASE WHEN ls.status IN ('INITIATED') THEN ls.amount ELSE 0 END) as "Available_supply_to_deploy",
                SUM(CASE WHEN ls.tenure = 5 AND ls.status = 'INITIATED' THEN ls.amount ELSE 0 END) as "Available_5M_supply_to_deploy",
                SUM(CASE WHEN ls.tenure = 7 AND ls.status = 'INITIATED' THEN ls.amount ELSE 0 END) as "Available_7M_supply_to_deploy",
                SUM(CASE WHEN ls.tenure = 14 AND ls.status = 'INITIATED' THEN ls.amount ELSE 0 END) as "Available_14_supply_to_deploy"
            FROM lendenapp_schemeinfo ls
            INNER JOIN lendenapp_transaction ON lendenapp_transaction.id = ls.transaction_id
            INNER JOIN lendenapp_user_source_group lusg ON lusg.id = ls.user_source_group_id
            INNER JOIN lendenapp_source ls2 ON ls2.id = lusg.source_id
            WHERE lendenapp_transaction."date"::date >= (
                SELECT MIN(created_date::date) 
                FROM lendenapp_schemeinfo 
                WHERE status = 'INITIATED' 
                AND investment_type = ANY(ARRAY['ONE_TIME_LENDING', 'MEDIUM_TERM_LENDING'])
            )
            AND lendenapp_transaction."date"::date BETWEEN %(start_date)s AND %(end_date)s
            AND ls.status = ANY(ARRAY['INITIATED', 'SUCCESS'])
            AND ls.tenure = ANY(ARRAY[5, 7, 14])
            GROUP BY 
                lendenapp_transaction."date"::date,
                ls2.source_name
            ORDER BY 
                lendenapp_transaction."date"::date DESC;
        """
        params = {'start_date': start_date, 'end_date': end_date}
        
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_pending_supply_date_wise(start_date, end_date):
        query = f"""
            SELECT 
            lendenapp_transaction."date"::date as "Date",
            CASE
                WHEN ls2.source_name = ANY(ARRAY['{InvestorSource.LCP}', '{InvestorSource.MCP}']) THEN 'CP'
                WHEN ls2.source_name = '{InvestorSource.LDC}' THEN 'Retail'
            END 
            as source_group_name,
            sum(case when ls.tenure = 5 and ls.status= 'INITIATED' then ls.amount else 0 end) as "Available_5M_supply_to_deploy",
            sum(case when ls.tenure = 7 and ls.status= 'INITIATED' then ls.amount else 0 end) as "Available_7M_supply_to_deploy",
            sum(case when ls.tenure = 11 and ls.status= 'INITIATED' then ls.amount else 0 end) as "Available_11M_supply_to_deploy",
            sum(case when ls.tenure = 14 and ls.status= 'INITIATED' 
                and (select product_type from lendenapp_otl_scheme_tracker lost 
                     where is_latest and lost.scheme_id = ls.scheme_id) = 'DAILY' 
                then ls.amount else 0 end) as "Available_14D_supply_to_deploy",
            sum(case when ls.tenure = 14 and ls.status= 'INITIATED' 
                and (select product_type from lendenapp_otl_scheme_tracker lost 
                     where is_latest and lost.scheme_id = ls.scheme_id) = 'MONTHLY' 
                then ls.amount else 0 end) as "Available_14M_supply_to_deploy"
        FROM lendenapp_schemeinfo ls
        INNER JOIN lendenapp_transaction ON lendenapp_transaction.id = ls.transaction_id 
        INNER JOIN lendenapp_user_source_group lusg ON lusg.id = ls.user_source_group_id
        INNER JOIN lendenapp_source ls2 on lusg.source_id = ls2.id
        WHERE lendenapp_transaction."date"::date >= (
            SELECT min(created_date::date) 
            FROM lendenapp_schemeinfo 
            WHERE status = 'INITIATED' 
            AND investment_type = ANY(ARRAY['ONE_TIME_LENDING','MEDIUM_TERM_LENDING'])
        ) 
        AND ls2.source_name = ANY(ARRAY['{InvestorSource.LCP}', '{InvestorSource.MCP}', '{InvestorSource.LDC}'])
        AND ls.status = ANY(ARRAY['INITIATED', 'SUCCESS'])
        AND ls.tenure = ANY(ARRAY[5, 7, 11, 14])
        AND lendenapp_transaction."date"::date BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY 
            CASE
                WHEN ls2.source_name = ANY(ARRAY['{InvestorSource.LCP}', '{InvestorSource.MCP}']) THEN 'CP'
                WHEN ls2.source_name = '{InvestorSource.LDC}' THEN 'Retail'
                end,
                lendenapp_transaction."date"::date
        ORDER BY lendenapp_transaction."date"::date DESC, source_group_name
        """
        
        params = {'start_date': start_date, 'end_date': end_date}
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)


    def fetch_investor_details(self, data):
        sql = f"""
            select lc2.partner_id, ls.source_name as partner_code,
            lc3.first_name as cp_name, lc.user_id, 
            lc.first_name, lc.gender, lc.encoded_mobile as mobile_number, lc.encoded_email as email, 
            lc.dob, lc.encoded_pan as pan, lc.type, 
            lc.gross_annual_income, 
            la2.user_source_group_id, lt.checklist, 
            la2.created_date::date, la2.balance, la2.status, 
            la2.listed_date, la2.number
            from lendenapp_user_source_group lusg 
            join lendenapp_account la2 on lusg.id = la2.user_source_group_id 
            join lendenapp_task lt on lt.user_source_group_id = lusg.id
            join lendenapp_source ls on ls.id = lusg.source_id 
            join lendenapp_customuser lc on lc.id = lusg.user_id
            left join lendenapp_channelpartner lc2 on 
            lc2.id = lusg.channel_partner_id  
            left join lendenapp_customuser lc3 on lc3.id = lc2.user_id 
            WHERE lusg.group_id = %(group)s 
            """

        params = {
                'group': UserGroup.LENDER,
            }

        search = data.get('search')
        search_query_type = data.get('search_query_type')

        if search:
            sql += f" and {InvestorMapper.dashboard_search_sql_query(params, search, search_query_type)}"

        if not data["is_download"]:
            params['limit'] = data['limit']
            params['offset'] = data['offset']
            sql += " LIMIT %(limit)s OFFSET %(offset)s"

        return DashboardMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def fetch_investor_profile_data(self, user_source_group_id):
        sql=f"""select lc2.partner_id, ls.source_name as partner_code,
            lc3.first_name as cp_name, lc.user_id, lc.id as user_pk,
            lc.first_name, lc.gender, lc.encoded_mobile as mobile_number, lc.encoded_email as email, 
            lc.dob, lc.encoded_pan as pan, lc.type, 
            lc.gross_annual_income, lc.mnrl_status,
            la2.user_source_group_id, lt.checklist, 
            la2.created_date::date, la2.balance, la2.status, 
            la2.listed_date, la2.number,lba.number as bank_account_number,lba.type as bank_account_type,
            lba.ifsc_code as bank_account_ifsc_code
            from lendenapp_user_source_group lusg
            join lendenapp_account la2 on lusg.id = la2.user_source_group_id 
            join lendenapp_bankaccount lba on lba.user_source_group_id = lusg.id and lba.purpose = %(purpose)s
            join lendenapp_task lt on lt.user_source_group_id = lusg.id
            join lendenapp_source ls on ls.id = lusg.source_id 
            join lendenapp_customuser lc on lc.id = lusg.user_id
            left join lendenapp_channelpartner lc2 on 
            lc2.id = lusg.channel_partner_id  
            left join lendenapp_customuser lc3 on lc3.id = lc2.user_id 
            WHERE lusg.id = %(user_source_group_id)s 
            """

        params={
                'user_source_group_id': user_source_group_id,
                'purpose': AddBankAccountConstant.PRIMARY_PURPOSE
            }

        return DashboardMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_investor_transactions(user_source_group_id, limit=10, offset=0, start_date=None, end_date=None, transaction_type=None, transaction_id=None):
        """
        Fetch transactions for a specific user source group with pagination and filters
        
        Args:
            user_source_group_id: User source group ID
            limit: Number of transactions to fetch
            offset: Offset for pagination
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            transaction_type: Transaction type filter (optional)
            transaction_id: Transaction ID filter (optional)
            
        Returns:
            dict with transaction_count and transaction_list
        """
        # Build WHERE clauses for filters
        where_clauses = ["lt.user_source_group_id = %(user_source_group_id)s"]
        
        params = {'user_source_group_id': user_source_group_id}
        
        # Add date filters if provided
        if start_date:
            where_clauses.append("lt.date >= %(start_date)s")
            params['start_date'] = start_date
        
        if end_date:
            where_clauses.append("lt.date <= %(end_date)s")
            params['end_date'] = end_date
        
        # Add type filter if provided
        if transaction_type:
            where_clauses.append("lt.type = %(transaction_type)s")
            params['transaction_type'] = transaction_type
        
        # Add transaction_id filter if provided
        if transaction_id:
            where_clauses.append("lt.transaction_id = %(transaction_id)s")
            params['transaction_id'] = transaction_id
        
        where_clause = " AND ".join(where_clauses)
        
        # First, get the total count
        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM lendenapp_transaction lt
            WHERE {where_clause}
        """
        
        count_result = DashboardMapper().sql_execute_fetch_one(count_query, params, to_dict=True)
        total_count = count_result.get('total_count', 0) if count_result else 0
        
        # Then fetch the transactions with pagination
        params['limit'] = limit
        params['offset'] = offset
        
        query = f"""
            SELECT
                lt.transaction_id,
                lt.amount,
                lt.status,
                lt.type,
                lt.created_date,
                lb.number as bank_account_number
            FROM
                lendenapp_transaction lt
            LEFT JOIN
                lendenapp_bankaccount lb ON lt.bank_account_id = lb.id
            WHERE 
                {where_clause}
            ORDER BY 
                lt.created_date DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        transactions = DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)
        
        return {
            'transaction_count': total_count,
            'transaction_list': transactions or []
        }

    @staticmethod
    def fetch_nominee_details(user_source_group_id):
        """
        Fetch nominee details for a specific user source group
        
        Args:
            user_source_group_id: User source group ID
            
        Returns:
            dict with nominee details or None if not found
        """
        query = """
            SELECT
                lr.name as full_name,
                lr.dob as nominee_dob,
                lr.relation as nominee_relation,
                lr.mobile_number,
                lr.email as nominee_email,
                lr.type as nominee_type
            FROM
                lendenapp_reference lr
            WHERE
                lr.user_source_group_id = %(user_source_group_id)s
                AND lr.type = %(type)s
        """
        
        params = {'user_source_group_id': user_source_group_id, 'type': NomineeType.NOMINEE}
        
        return DashboardMapper().sql_execute_fetch_one(query, params, to_dict=True)

    @staticmethod
    def fetch_user_bank_account_details(user_source_group_id):
        """
        Fetch detailed bank account information for a user
        """
        query = """
            SELECT 
                lba.id as bank_id,
                lba.number as acc_number,
                lba.type,
                lba.ifsc_code,
                lba.purpose as acc_status
            FROM 
                lendenapp_bankaccount lba 
            WHERE 
                lba.user_source_group_id = %(user_source_group_id)s
                AND lba.is_active = True
        """
        
        params = {'user_source_group_id': user_source_group_id}
        
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def fetch_rm_name_by_user_id(user_source_group_id):
        query = """
            SELECT 
                lr.name 
            FROM 
                lendenapp_reference lr
            WHERE
                lr.user_source_group_id = %(user_source_group_id)s
                AND lr.relation = %(relation)s
        """
        
        params = {'user_source_group_id': user_source_group_id, 'relation': ReferenceConstant.RELATION_RM}
        
        return DashboardMapper().sql_execute_fetch_one(query, params, to_dict=True)
