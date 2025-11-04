import datetime
import pydantic
import typing
import sipametrics.internal.markers as _markers
import sipametrics.internal.permissions as _permissions
import sipametrics.internal.endpoints as _endpoints
import sipametrics.internal.clients as _clients
import sipametrics.models.metrics as metrics_models
import sipametrics.models.pi_comparables as pi_comparables_models, sipametrics.models.pe_comparables as pe_comparables_models
import sipametrics.models.term_structures as term_structures_models
import sipametrics.models.indices_catalogue as indices_catalogue_models
import sipametrics.models.metrics_catalogue as metrics_catalogue_models
import sipametrics.models.taxonomies as taxonomies_models
import sipametrics.models.custom_benchmarks as custom_benchmarks_models
import sipametrics.models.direct_alpha as direct_alpha_models
import sipametrics.constants as CONSTANTS


class SipaMetricsService:
    def __init__(self, api_key: str, api_secret: str):
        self.client = _clients.BaseClient(api_key, api_secret)

    async def close(self):
        await self.client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, tb):
        await self.client.close()


    ######
    # Metrics
    ######
    async def metrics(self, 
                      entity_id: typing.Union[list[str], str], 
                      metric_id: typing.Union[list[str], str]) -> dict:
        """
        Returns data for metrics of a given index or a list of indices. Refer to https://docs.sipametrics.com/docs/2-2-1-quick-start for details.

        Args:
            entity_id (str or list of str): One or more index tickers.
            metric_id (str or list of str): One or more metric tickers.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            request = metrics_models.MetricsRequest(entity_id=entity_id, metric_id=metric_id)
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")
        
        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.metrics.__name__], data=params)    


    ######
    # PI Comparables
    ######
    async def infra_equity_comparable(
        self,
        metric: str,
        currency: typing.Optional[str] = None,
        age_in_months: typing.Optional[int] = None,
        end_date: typing.Optional[datetime.date] = None,
        window_in_years: typing.Optional[int] = None,
        industrial_activities: typing.Optional[list[str]] = None,
        business_risk: typing.Optional[str] = None,
        corporate_structure: typing.Optional[str] = None,
        countries: typing.Optional[list[str]] = None,
        size: typing.Optional[typing.Union[float, str]] = None,
        leverage: typing.Optional[typing.Union[float, str]] = None,
        profitability: typing.Optional[typing.Union[float, str]] = None,
        investment: typing.Optional[typing.Union[float, str]] = None,
        time_to_maturity: typing.Optional[typing.Union[float, str]] = None,
        factor_weight: typing.Optional[float] = None,
        intersect_ticcs: typing.Optional[bool] = None,
    ) -> dict:
        """
        Performs a comparable computation for private infrastructure equities. This involves finding data points which have similar TICCS classifications and factor values,
        and averaging the metric values. Refer to https://docs.sipametrics.com/docs/2-3-2-sipametrics-infra_equity_comparable for more details.

        Args:
            metric (str): The metric for which the comparable has to be evaluated.
            currency (str, optional): The currency of monetary factor inputs such as size.
            age_in_months (int, optional): The age of the company in months. If this parameter is set, end_date and window_in_years will be ignored.
            end_date (date, optional): The maximum date of the comparable dataset.
            window_in_years (int, optional): The window in years of the comparable dataset.
            industrial_activities (list of str, optional): List of industrial activity TICCS codes.
            business_risk (str, optional): Business risk TICCS code.
            corporate_structure (str, optional): Corporate structure TICCS code.
            countries (list of str, optional): List of country ISO codes.
            size (float or str, optional): Total assets or size of the company. Represented either as an absolute value in millions of the specified currency or as a
                quintile value.
            leverage (float or str, optional): Total senior liabilities over total assets. Represented either as a percentage or as a quintile value.
            profitability (float or str, optional): Return on assets or profitability metric. Represented either as a percentage or as a quintile value.
            investment (float or str, optional): Capital expenditures over total assets. Represented either as a percentage or as a quintile value.
            time_to_maturity (float or str, optional): Years until maturity. Represented as either a numerical value or as a bucket.
            factor_weight (float, optional):
            intersect_ticcs (bool, optional): 

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            ticcs_profile = pi_comparables_models.TiccsProfile(
                industrial_activities=industrial_activities,
                business_risk=business_risk,
                corporate_structure=corporate_structure
            )
            factors_profile = pi_comparables_models.EquityFactorProfile(
                currency=currency,
                countries=countries,
                size=size,
                leverage=leverage,
                profitability=profitability,
                investment=investment,
                time_to_maturity=time_to_maturity
            )
            request = pi_comparables_models.ComparableRequest(
                metric=metric,
                age_in_months=age_in_months,
                end_date=end_date,
                window_in_years=window_in_years,
                ticcs_profiles=ticcs_profile,
                factors_profiles=factors_profile,
                factor_weight=factor_weight,
                intersect_ticcs=intersect_ticcs,
            )
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")
        
        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.infra_equity_comparable.__name__], data=params)    

    async def infra_debt_comparable(
        self,
        metric: str,
        currency: typing.Optional[str] = None,
        age_in_months: typing.Optional[int] = None,
        end_date: typing.Optional[datetime.date] = None,
        window_in_years: typing.Optional[int] = None,
        industrial_activities: typing.Optional[list[str]] = None,
        business_risk: typing.Optional[str] = None,
        corporate_structure: typing.Optional[str] = None,
        countries: typing.Optional[list[str]] = None,
        face_value: typing.Optional[typing.Union[float, str]] = None,
        time_to_maturity: typing.Optional[typing.Union[float, str]] = None,
        factor_weight: typing.Optional[float] = None,
        intersect_ticcs: typing.Optional[bool] = None,        
    ) -> dict:
        """
        Perform a comparable computation for private infrastructure debts. This involves finding datapoints which have similar TICCS classifications and factor values,
        and averaging the metric values. Refer to https://docs.sipametrics.com/docs/2-3-3-sipametrics-infra_debt_comparable for more information.

        Args:
            metric (str): The metric for which the comparable has to be evaluated.
            currency (str, optional): The currency of monetary factor inputs such as size.
            age_in_months (int, optional): The age of the company in months.
            end_date (date, optional): The maximum date of the comparable dataset.
            window_in_years (int, optional): The window in years of the comparable dataset.
            industrial_activities (list of str, optional): List of industrial activity TICCS codes.
            business_risk (str, optional): Business risk TICCS code.
            corporate_structure (str, optional): Corporate structure TICCS code.
            countries (list of str, optional): List of country ISO codes.
            face_value (float or str, optional): Face value of assets, represented either as an absolute value in millions of the specified currency or as a
                quintile value.
            time_to_maturity (float or str, optional): Years until maturity. Represented as either a numerical value or as a bucket.
            factor_weight (float, optional):
            intersect_ticcs (bool, optional): 

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            ticcs_profile = pi_comparables_models.TiccsProfile(
                industrial_activities=industrial_activities,
                business_risk=business_risk,
                corporate_structure=corporate_structure
            )
            factors_profile = pi_comparables_models.DebtFactorProfile(
                currency=currency,
                countries=countries,
                face_value=face_value,
                time_to_maturity=time_to_maturity
            )  
            request = pi_comparables_models.ComparableRequest(
                metric=metric,
                age_in_months=age_in_months,
                end_date=end_date,
                window_in_years=window_in_years,
                ticcs_profiles=ticcs_profile,
                factors_profiles=factors_profile,
                factor_weight=factor_weight,
                intersect_ticcs=intersect_ticcs,
            )      
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")
        
        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.infra_debt_comparable.__name__], data=params)  


    ######
    # Term Structure
    ######
    async def term_structure(self, country: str, date: datetime.date, maturity_date: datetime.date) -> dict:
        """
        Query annualised risk-free rate for a given country and maturity date on the curve. Refer to https://docs.sipametrics.com/docs/2-3-4-sipametrics-termstructure for
        more information.

        Args:
            country (str): Three-letter ISO code representing the country.
            date (date): Date in point.
            maturity_date (date): Maturity date of the term structure.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            request = term_structures_models.TermStructureRequest(
                country=country,
                date=date,
                maturity_date=maturity_date
            )
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")
        
        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.term_structure.__name__], data=params)


    ######
    # PE Comparables
    ######
    async def private_equity_comparable(
        self,
        metric: str,
        currency: typing.Optional[str] = None,
        age_in_months: typing.Optional[int] = None,
        end_date: typing.Optional[datetime.date] = None,
        window_in_years: typing.Optional[int] = None,
        industrial_activities: typing.Optional[list[str]] = None,
        revenue_models: typing.Optional[list[str]] = None,
        customer_models: typing.Optional[list[str]] = None,
        lifecycle_phases: typing.Optional[list[str]] = None,
        value_chain_types: typing.Optional[list[str]] = None,
        countries: typing.Optional[list[str]] = None,
        size: typing.Optional[typing.Union[float, str]] = None,
        growth: typing.Optional[typing.Union[float, str]] = None,
        leverage: typing.Optional[typing.Union[float, str]] = None,
        profits: typing.Optional[typing.Union[float, str]] = None,
        country_risk: typing.Optional[list[str]] = None,
        universe: typing.Optional[str] = None,
        factor_weight: typing.Optional[float] = None,
        type: typing.Optional[str] = "mean",
        intersect_peccs: typing.Optional[bool] = None,
    ) -> dict:
        """
        Perform a comparable computation for private equities. This involves finding datapoints which have similar PECCS classifications and factor values and
        averaging the metric values. Refer to https://docs.sipametrics.com/docs/2-3-5-sipametrics-private_equity_comparable for more information.

        Args:
            metric (str): The metric for which the comparable has to be evaluated.
            currency (str, optional): The currency of monetary factor inputs such as size.
            age_in_months (int, optional): The age of the company in months.
            end_date (date, optional): The maximum date of the comparable dataset.
            window_in_years (int, optional): The window in years of the comparable dataset. 
            industrial_activities (list of str, optional): List of industrial activity PECCS codes.
            revenue_models (list of str, optional): List of revenue model PECCS codes.
            customer_models (list of str, optional): List of customer model PECCS codes.
            lifecycle_phases (list of str, optional): List of lifecycle phase PECCS codes.
            value_chain_types (list of str, optional): List of value chain type PECCS codes.
            countries (list of str, optional): List of country ISO codes.
            size (float or str, optional): Revenue of the company. Represented either as an absolute value in millions of the specified currency or as a quintile value.
            growth (float or str, optional): Revenue growth. Represented either as a percentage or as a quintile value.
            leverage (float or str, optional): Total senior liabilities over total assets. Represented either as a percentage or as a quintile value.
            profits (float or str, optional): EBITDA margin. Represented either as a percentage or as a quintile value.
            country_risk (list of str, optional): Term spread. Specified as a list of country ISO codes.
            universe (str, optional): Universe of companies in the dataset.
            factor_weight (float, optional): A decimal value between 0 and 1. At the extremes, 1 indicates that comparables are purely based on factors, while 0
                indicates that comparables are purely based on PECCS. Values between 0 and 1 create a weighted average between the two.
            type (str, optional): Determines how to aggregate the comparables dataset. Default is "mean".
            intersect_peccs (bool, optional): Determines whether to intersect the PECCS codes. Default is True.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            peccs_country_profile = pe_comparables_models.PeccsCountryProfile(
                industrial_activities=industrial_activities,
                revenue_models=revenue_models,
                customer_models=customer_models,
                lifecycle_phases=lifecycle_phases,
                value_chain_types=value_chain_types,
                countries=countries
            )
            factors_profile = pe_comparables_models.FactorProfile(
                size=size,
                growth=growth,
                leverage=leverage,
                profits=profits,
                country_risk=country_risk
            )
            request = pe_comparables_models.ComparableRequest(
                metric=metric,
                age_in_months=age_in_months,
                end_date=end_date,
                window_in_years=window_in_years,
                peccs_country_profile=peccs_country_profile,
                factors_profiles=factors_profile,
                currency=currency,
                universe=universe,
                factor_weight=factor_weight,
                operation=type,
                intersect_peccs=intersect_peccs
            )
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")
        
        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.private_equity_comparable.__name__], data=params)
 
    async def private_equity_comparable_boundaries(
        self,
        metric: str,
        factor_name: str,
        currency: typing.Optional[str] = None,
        age_in_months: typing.Optional[int] = None,
        end_date: typing.Optional[datetime.date] = None,
        window_in_years: typing.Optional[int] = None,
        industrial_activities: typing.Optional[list[str]] = None,
        revenue_models: typing.Optional[list[str]] = None,
        customer_models: typing.Optional[list[str]] = None,
        lifecycle_phases: typing.Optional[list[str]] = None,
        value_chain_types: typing.Optional[list[str]] = None,
        countries: typing.Optional[list[str]] = None,
        universe: typing.Optional[str] = None
    ) -> dict:
        """
        Evaluates the quintile boundaries for a given metric within the private equity comparables dataset. Refer to 
        https://docs.sipametrics.com/docs/2-3-6-sipametrics-private_equity_comparable_bounda for more information.

        Args:
            metric (str): The metric for which the comparable has to be evaluated.
            factor_name (str): The factor for which to obtain the quintile boundaries.
            currency (str, optional): The currency of monetary factor inputs, such as size.
            age_in_months (int, optional): The age of the company in months. 
            end_date (date, optional): The maximum date of the comparable dataset.
            window_in_years (int, optional): The window in years of the comparable dataset.
            industrial_activities (list of str, optional): List of industrial activity PECCS codes.
            revenue_models (list of str, optional): List of revenue model PECCS codes.
            customer_models (list of str, optional): List of customer model PECCS codes.
            lifecycle_phases (list of str, optional): List of lifecycle phase PECCS codes.
            value_chain_types (list of str, optional): List of value chain type PECCS codes.
            countries (list of str, optional): List of country ISO codes.
            universe (str, optional): Universe of companies in the dataset.
        
        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            peccs_country_profile = pe_comparables_models.PeccsCountryProfile(
                industrial_activities=industrial_activities,
                revenue_models=revenue_models,
                customer_models=customer_models,
                lifecycle_phases=lifecycle_phases,
                value_chain_types=value_chain_types,
                countries=countries
            )
            request = pe_comparables_models.ComparableBoundaryRequest(
                metric=metric,
                currency=currency,
                factor_name=factor_name,
                age_in_months=age_in_months,
                end_date=end_date,
                window_in_years=window_in_years,
                peccs_country_profile=peccs_country_profile,
                universe=universe
            )
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")
        
        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.private_equity_comparable_boundaries.__name__], data=params)


    ######
    # Indices Catalogue
    ######
    async def indices_catalogue(
        self, 
        product: CONSTANTS.Product, 
        app: typing.Optional[CONSTANTS.App] = None
    ) -> dict:
        """
        List of indices, as well as the corresponding categories and tickers. Refer to https://docs.sipametrics.com/docs/2-3-7-sipametrics-indices_catalogue for
        more information.

        Args:
            product (str): Type of product.
            app (App, optional): App within the product. If this is supplied, an additional hasAccess property would be added in the results as a permission indicator.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            request = indices_catalogue_models.IndicesCatalogueRequest(product=product, app=app)
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")
        
        params = request.to_dict()
        results = await self.client._get(_endpoints.URLS[self.indices_catalogue.__name__], params=params)

        if app is None:
            return results
        
        if "data" in results and "results" in results["data"]:
            indices:list[dict] = results["data"]["results"]
            if not indices:
                return results
            
            index_tickers = [index["externalTicker"] for index in indices]
            if app == CONSTANTS.App.VALUATION:
                metric_tickers = ["T02806"]
                action_name = "DOWNLOAD_VALUATION"
            elif app == CONSTANTS.App.THEMATIC_INDICES:
                metric_tickers = ["T01414"]
                action_name = "DOWNLOAD_TICCS_RESEARCH_DATA"
            else:
                metric_tickers = ["T01414"]
                action_name = "DOWNLOAD_INDEX_DATA"
            
            permissions_map = {}
            permissions = await _permissions._check_permissions(self.client, index_tickers=index_tickers, metric_tickers=metric_tickers, action_name=action_name)
            if permissions and "permissions" in permissions:
                permissions_map = { permission["resourceTicker"]: permission["permitted"] for permission in permissions["permissions"] }

            for index in indices:
                index["hasAccess"] = permissions_map.get(index["externalTicker"], False)

        return results
    
    ######
    # Metrics Catalogue
    ######
    async def metrics_catalogue(
        self, 
        product: CONSTANTS.Product, 
        app: CONSTANTS.App,
        asset_class: typing.Optional[CONSTANTS.AssetClass] = None,
    ) -> dict:
        """
        List of metrics as well as the corresponding categories and tickers.

        Args:
            product (str): Type of product.
            app (App, optional): App within the product.
            asset_class: Asset class.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            request = metrics_catalogue_models.MetricsCatalogueRequest(product=product, app=app, asset_class=asset_class)
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        if product == CONSTANTS.Product.PRIVATE_INFRA:
            app_key = "ticcs-benchmarks" if app == CONSTANTS.App.THEMATIC_INDICES else app.value
        elif product == CONSTANTS.Product.PRIVATE_EQUITY:
            app_key = "peccs-benchmarks" if app == CONSTANTS.App.THEMATIC_INDICES else app.value
        else:
            app_key = app.value
        destined_url = _endpoints.URLS[self.metrics_catalogue.__name__].format(app=app_key)

        params = request.to_dict()
        results = await self.client._get(destined_url, params=params)
        return results    

    ######
    # Taxonomies
    ######
    async def taxonomies(
            self, 
            taxonomy: CONSTANTS.Taxonomy, 
            pillar: typing.Optional[typing.Union[CONSTANTS.Ticcs, CONSTANTS.Peccs]] = None
    ) -> dict:
        """
        Retrieves a list of supported taxonomy (TICCS®, PECCS®, and TICCS®+) definitions and the relevant mappings. Refer to 
        https://docs.sipametrics.com/docs/2-3-8-sipametrics-taxonomies for more information.

        Args:
            taxonomy (str): The taxonomy to query.
            pillar (Ticcs, Peccs, optional): The pillar within the taxonomy to be queried.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            request = taxonomies_models.TaxonomiesRequest(taxonomy=taxonomy, pillar=pillar)
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        params = request.to_dict()
        destined_url = _endpoints.URLS[self.taxonomies.__name__].format(taxonomy=params["taxonomy"])
        return await self.client._get(destined_url, params={ "pillar": params["pillar"] })


    ######
    # PE Custom Benchmarks
    ######
    @_markers.beta
    async def private_equity_custom_benchmarks(
        self,
        index_ticker: str,
        start_date: typing.Optional[datetime.date] = None,
        end_date: typing.Optional[datetime.date] = None,
        currency: typing.Optional[str] = None,
        constraints: typing.Optional[list[typing.Union[custom_benchmarks_models.Constraint, custom_benchmarks_models.EqualityConstraint, custom_benchmarks_models.RangeConstraint]]] = None,
        initial_index_value: typing.Optional[float] = None,
        allocations: typing.Optional[bool] = None,
        risk_profiles: typing.Optional[bool] = None,
        include_constituents: typing.Optional[bool] = None,
    ) -> dict:
        """
        To generate custom benchmarks based on an existing private equity index, with the option to modify the weightage of constituents by constraints. Refer to 
        https://docs.sipametrics.com/docs/2-3-9-private_equity_custom_benchmarks for more information.

        Args:
            index_ticker (str): Ticker of the index.
            start_date (date, optional): Start date of the index.
            end_date (date, optional): End date of the index.
            currency (str, optional): The reporting currency.
            constraints (list of EqualityConstraint, list of RangeConstraint, list of Constraint, optional): List of constraints to be applied to the index.
            initial_index_value (float, optional): Initial index value.
            allocations (bool, optional): Whether to include PECCS allocations. Default is False.
            risk_profiles (bool, optional): Whether to include risk profiles. Default is False.
            include_constituents (bool, optional): Whether to include list of constituents. Default is False.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
           request = custom_benchmarks_models.CustomBenchmarkRequest(
                external_ticker=index_ticker,
                start_date=start_date,
                end_date=end_date,
                currency=currency,
                constraints=constraints,
                initial_index_value=initial_index_value,
                allocations=allocations,
                risk_profiles=risk_profiles,
                include_constituents=include_constituents
            )
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.private_equity_custom_benchmarks.__name__], data=params) 


    ######
    # PE Region Tree
    ######
    async def private_equity_region_tree(self) -> dict:
        """
        Returns hierarchical view of regions, subregions and countries within private equity universe. Refer to
        https://docs.sipametrics.com/docs/2-3-10-sipametrics-private_equity_region_tree for more information.

        Returns:
            dict: Results wrapped in 'data' element.
        """
        return await self.client._get(_endpoints.URLS[self.private_equity_region_tree.__name__])


    ######
    # PI Custom Benchmarks
    ######
    @_markers.beta
    async def private_infra_custom_benchmarks(
        self,
        index_ticker: str,
        start_date: typing.Optional[datetime.date] = None,
        end_date: typing.Optional[datetime.date] = None,
        currency: typing.Optional[str] = None,
        constraints: typing.Optional[list[typing.Union[custom_benchmarks_models.Constraint, custom_benchmarks_models.EqualityConstraint, custom_benchmarks_models.RangeConstraint]]] = None,
        initial_index_value: typing.Optional[float] = None,
        allocations: typing.Optional[bool] = None,
        risk_profiles: typing.Optional[bool] = None,
        include_constituents: typing.Optional[bool] = None,
    ) -> dict:
        """
        To generate custom benchmarks based on an existing private infrastructure index, with the option to modify the weightage of constituents by constraints. 

        Args:
            index_ticker (str): Ticker of the index.
            start_date (date, optional): Start date of the index.
            end_date (date, optional): End date of the index.
            currency (str, optional): The reporting currency.
            constraints (list of Constraint, optional): List of constraints to be applied to the index.
            initial_index_value (float, optional): Initial index value.
            allocations (bool, optional): Whether to include TICCS allocations.
            risk_profiles (bool, optional): Whether to include risk profiles.
            include_constituents (bool, optional): Whether to include list of constituents.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
           request = custom_benchmarks_models.CustomBenchmarkRequest(
                external_ticker=index_ticker,
                start_date=start_date,
                end_date=end_date,
                currency=currency,
                constraints=constraints,
                initial_index_value=initial_index_value,
                allocations=allocations,
                risk_profiles=risk_profiles,
                include_constituents=include_constituents
            )
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.private_infra_custom_benchmarks.__name__], data=params) 


    ######
    # Direct Alpha
    ######    
    @_markers.beta
    async def direct_alpha(
        self,
        data: list[direct_alpha_models.FundAlphaData]
    ) -> dict:
        """
        Produce alpha comparison for a fund against a broadmarket index and optionally a benchmark index.

        Args:
            data (list of FundAlphaData): External ticker of the index.

        Returns:
            dict: Results wrapped in 'data' element.

        Raises:
            ValueError: If one or more arguments contain invalid or unsupported values.
        """
        try:
            request = direct_alpha_models.AlphaRequest(
                fund_alpha_data=data,
            )
        except pydantic.ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        params = request.to_dict()
        return await self.client._post(_endpoints.URLS[self.direct_alpha.__name__], data=params) 
