from flask import Flask, render_template, request, redirect
from datetime import date
import mysql.connector

# contains helper functions (validators and checkers)
import helper

app = Flask(__name__)

# establish connection to DB
def connect_to_db():
    connection = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="EastWind_131965", # edit password
        database="dbelectric"
    )
    return connection

# route to home
@app.route('/')
def index():
    return render_template('HomePage.html')

# route to services
@app.route('/services')
def services():
    try:
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT service_id, service_type, service_fee, description 
            FROM services 
        """)
        services = cursor.fetchall()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        services = []
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('ServicesPage.html', services=services)

# managing services
@app.route('/services/manage', methods=['GET', 'POST'])
def manage_service(service_id=None):
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        service_type = request.form['serviceType']
        service_fee = request.form['serviceFee']
        description = request.form['description']
        selected_service = request.form.get('existingServices')

        if selected_service:
            cursor.execute("""
                UPDATE services
                SET service_type = %s, service_fee = %s, description = %s
                WHERE service_id = %s
            """, (service_type, service_fee, description, selected_service))

        connection.commit()
        connection.close()
        return redirect('/services')

    if service_id: 
        cursor.execute("""
            SELECT service_id, service_type, service_fee, description
            FROM services
            WHERE service_id = %s
        """, (service_id,))
        service = cursor.fetchone()
    else: 
        service = None

    cursor.execute("SELECT service_id, service_type, service_fee, description FROM services")
    all_services = cursor.fetchall()
    connection.close()
    return render_template('InputService.html', service=service, all_services=all_services)

# contractors page
@app.route('/contractors', methods=['GET', 'POST'])
def contractors():
    try:
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # Get all available services for the filter dropdown
        cursor.execute("SELECT service_type FROM services")
        services = cursor.fetchall()

        # Get the filter values from the request
        status_filter = request.args.get('statusFilter')
        last_name_filter = request.args.get('lastNameFilter')
        first_name_filter = request.args.get('firstNameFilter')

        # Base query to retrieve contractors
        query = """
            SELECT c.contractor_id, c.job_title, c.last_name, c.first_name, c.contact_number, c.status, s.service_type AS specialization
            FROM contractors c
            JOIN services s ON c.service_id = s.service_id
        """
        
        conditions = []
        params = []

        # Filter contractors based on user input
        if status_filter:
            conditions.append("c.status = %s")
            params.append(status_filter)

        if last_name_filter:
            conditions.append("c.last_name LIKE %s")
            params.append(f"%{last_name_filter}%")

        if first_name_filter:
            conditions.append("c.first_name LIKE %s")
            params.append(f"%{first_name_filter}%")

        # If filters exist, add them to the query
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Execute the query with any filters applied
        cursor.execute(query, params)
        contractors = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        contractors = []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    # Render the Contractors page with contractors and services data
    return render_template('ContractorsPage.html', contractors=contractors, services=services)

# route to contractors by service
@app.route('/contractorsByService/<service_id>')
def contractorsByService(service_id):
    try:
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT service_type FROM services WHERE service_id = %s", (service_id,))
        service = cursor.fetchone()

        cursor.execute("""
            SELECT c.contractor_id, c.job_title, c.last_name, c.first_name, c.contact_number, c.status, s.service_type AS specialization
            FROM contractors c
            JOIN services s ON c.service_id = s.service_id
            WHERE c.service_id = %s
        """, (service_id,))
        contractors = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        service = None
        contractors = []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
        
    return render_template('ContractorsPage.html', contractors=contractors, service_type=service['service_type'] if service else 'Unknown')

# route to customers
@app.route('/customers', methods=['GET'])
def customers():
    try:
        # Get filter values from the request
        status_filter = request.args.get('statusFilter', '')
        last_name_filter = request.args.get('lastNameFilter', '')
        first_name_filter = request.args.get('firstNameFilter', '')
        city_filter = request.args.get('cityFilter', '')

        # Construct base query
        query = """
            SELECT c.customer_id, c.last_name, c.first_name, c.contact_number, c.status,
            a.address_details, a.barangay, a.city, a.postal_code
            FROM customers c
            JOIN addresses a ON c.permanent_address = a.address_id
            WHERE 1=1
        """

        # Add filters to the query
        if status_filter:
            query += " AND c.status = %s"
        if last_name_filter:
            query += " AND c.last_name LIKE %s"
        if first_name_filter:
            query += " AND c.first_name LIKE %s"
        if city_filter:
            query += " AND a.city LIKE %s"

        # Prepare the parameters for the query
        params = []
        if status_filter:
            params.append(status_filter)
        if last_name_filter:
            params.append(f"%{last_name_filter}%")  # For partial search
        if first_name_filter:
            params.append(f"%{first_name_filter}%")  # For partial search
        if city_filter:
            params.append(f"%{city_filter}%")  # For partial search

        # Connect to the database
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # Execute the query with filters
        cursor.execute(query, params)
        customers = cursor.fetchall()

        if not customers:
            print("No customers found.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        customers = []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    # Render the template with the filtered customers list
    return render_template('CustomersPage.html', customers=customers)

# managing customers (input)
@app.route('/customers/<customer_id>', methods=['GET', 'POST'])
@app.route('/customers/new', methods=['GET', 'POST'])
def manage_customer(customer_id=None):
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        last_name = request.form['lastName']
        first_name = request.form['firstName']
        contact_number = request.form['contactNumber']
        address_details = request.form['addressDetails']
        barangay = request.form['barangay']
        city = request.form['city']
        postal_code = request.form['postalCode']

        if customer_id:
            cursor.execute("""
                UPDATE addresses
                SET address_details = %s, barangay = %s, city = %s, postal_code = %s
                WHERE address_id = (
                    SELECT permanent_address FROM customers WHERE customer_id = %s
                )
            """, (address_details, barangay, city, postal_code, customer_id))

            cursor.execute("""
                UPDATE customers
                SET last_name = %s, first_name = %s, contact_number = %s
                WHERE customer_id = %s
            """, (last_name, first_name, contact_number, customer_id))
        else:
            last_address_id = helper.generateID(cursor, "addresses", "address_id")
            last_customer_id = helper.generateID(cursor,  "customers", "customer_id")
            last_reg_id = helper.generateID(cursor, "customer_registration", "registration_id", "REG")
            current_date = date.today()

            cursor.execute("""
                INSERT INTO addresses (address_id, address_details, barangay, city, postal_code)
                VALUES (%s, %s, %s, %s, %s)
            """, (last_address_id, address_details, barangay, city, postal_code))

            cursor.execute("""
                INSERT INTO customers (customer_id, last_name, first_name, contact_number, permanent_address)
                VALUES (%s, %s, %s, %s, %s)
            """, (last_customer_id, last_name, first_name, contact_number, last_address_id))

            cursor.execute("""
                INSERT INTO customer_registration (registration_id, customer_id, date)
                VALUES (%s, %s, %s)
            """, (last_reg_id, last_customer_id, current_date))

        connection.commit()
        connection.close()
        return redirect('/customers')

    if customer_id:
        cursor.execute("""
            SELECT c.customer_id, c.last_name, c.first_name, c.contact_number,
                   a.address_details, a.barangay, a.city, a.postal_code
            FROM customers c
            JOIN addresses a ON c.permanent_address = a.address_id
            WHERE c.customer_id = %s
        """, (customer_id,))
        customer = cursor.fetchone()
    else:
        customer = None

    connection.close()
    return render_template('InputCustomer.html', customer=customer)

# managing contractors
@app.route('/contractors/<contractor_id>', methods=['GET', 'POST'])
@app.route('/contractors/new', methods=['GET', 'POST'])
def manage_contractor(contractor_id=None):
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        last_name = request.form['lastName']
        first_name = request.form['firstName']
        contact_number = request.form['contactNumber']
        job_title = request.form['jobTitle']
        service_id = request.form['serviceId']
        status = request.form['status']

        if contractor_id:
            # Update existing contractor
            cursor.execute("""
                UPDATE contractors
                SET last_name = %s, first_name = %s, contact_number = %s,
                    job_title = %s, service_id = %s, status = %s
                WHERE contractor_id = %s
            """, (last_name, first_name, contact_number, job_title, service_id, status, contractor_id))
        else:
            # Generate new IDs and insert a new contractor
            last_contractor_id = helper.generateID(cursor, "contractors", "contractor_id")
            last_reg_id = helper.generateID(cursor, "contractor_registration", "registration_id", "REG")
            current_date = date.today()

            cursor.execute("""
                INSERT INTO contractors (contractor_id, last_name, first_name, contact_number, job_title, service_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (last_contractor_id, last_name, first_name, contact_number, job_title, service_id, status))

            cursor.execute("""
                INSERT INTO contractor_registration (registration_id, contractor_id, date)
                VALUES (%s, %s, %s)
            """, (last_reg_id, last_contractor_id, current_date))

        connection.commit()
        connection.close()
        return redirect('/contractors')

    if contractor_id:
        # Fetch contractor details for editing
        cursor.execute("""
            SELECT c.contractor_id, c.last_name, c.first_name, c.contact_number,
                   c.job_title, c.service_id, c.status, s.service_type
            FROM contractors c
            LEFT JOIN services s ON c.service_id = s.service_id
            WHERE c.contractor_id = %s
        """, (contractor_id,))
        contractor = cursor.fetchone()
    else:
        contractor = None

    # Fetch all services for the dropdown
    cursor.execute("SELECT service_id, service_type FROM services")
    services = cursor.fetchall()

    connection.close()
    return render_template('InputContractor.html', contractor=contractor, services=services)

@app.route('/electricmeters', methods=['GET', 'POST'])
def electricMeters():
    try:
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # Get the filter values from the form
        year_filter = request.args.get('yearFilter')
        status_filter = request.args.get('statusFilter')
        acc_num_filter = request.args.get('accNumFilter')

        # Get distinct years for the dropdown
        cursor.execute("SELECT DISTINCT YEAR(installation_date) AS year FROM meters ORDER BY year DESC")
        years = cursor.fetchall()

        # Base query
        query = """
            SELECT 
                m.meter_id, m.account_number, m.installation_date, m.status, 
                c.last_name, c.first_name,
                a.address_details, a.barangay, a.city, a.postal_code
            FROM meters m
            JOIN customers c ON m.customer_id = c.customer_id
            JOIN addresses a ON m.install_address = a.address_id
        """

        # Add conditions based on the filters
        conditions = []
        if year_filter and year_filter != "-- Select Year --":
            conditions.append(f"YEAR(m.installation_date) = {year_filter}")
        if status_filter and status_filter != "-- Select Status --":
            conditions.append(f"m.status = '{status_filter}'")
        if acc_num_filter:
            conditions.append(f"m.account_number LIKE '%{acc_num_filter}%'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query)
        meters = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        meters = []
        years = []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return render_template('ElectricMetersPage.html', meters=meters, years=years)

@app.route('/registration', methods=['GET'])
def registration():
    connection = connect_to_db()
    selected_tab = request.args.get('tab', 'customer')
    try:
        with connection.cursor(dictionary=True) as cursor:
            if selected_tab == 'customer':
                cursor.execute("SELECT c.registration_id, cu.first_name, cu.last_name, c.date "
                               "FROM customer_registration c "
                               "JOIN customers cu ON c.customer_id = cu.customer_id "
                               "ORDER BY c.date DESC, c.registration_id DESC")
                customer_records = cursor.fetchall()
                contractor_records = []
            else:
                cursor.execute("SELECT cr.registration_id, co.first_name, co.last_name, cr.date "
                               "FROM contractor_registration cr "
                               "JOIN contractors co ON cr.contractor_id = co.contractor_id "
                               "ORDER BY cr.date DESC, cr.registration_id DESC")
                contractor_records = cursor.fetchall()
                customer_records = []

    finally:
        connection.close()

    return render_template(
        'Registration.html',
        selected_tab=selected_tab,
        customer_records=customer_records,
        contractor_records=contractor_records
    )

@app.route('/services-availed', methods=['GET'])
def services_availed():
    selected_year = request.args.get('year')
    selected_service_type = request.args.get('service_type')
    contractor_id = request.args.get('contractor_id')  # Get contractor ID from query params

    connection = connect_to_db()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch distinct service types for the filter dropdown
            cursor.execute("SELECT DISTINCT service_type FROM services")
            service_types = [row['service_type'] for row in cursor.fetchall()]

            # Base query for services availed
            query = """
                SELECT 
                    s.service_type AS service_name,
                    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
                    m.account_number AS customer_account,
                    CONCAT(con.first_name, ' ', con.last_name) AS contractor_name,
                    DATE_FORMAT(sa.date, '%Y-%m-%d') AS date
                FROM services_availed sa
                JOIN customers c ON sa.customer_id = c.customer_id
                JOIN meters m ON sa.meter_id = m.meter_id
                JOIN services s ON sa.service_id = s.service_id
                JOIN contractors con ON sa.contractor_id = con.contractor_id
                WHERE 1 = 1
            """
            params = []

            # Filter by year if selected
            if selected_year:
                query += " AND YEAR(sa.date) = %s"
                params.append(selected_year)

            # Filter by service type if selected
            if selected_service_type:
                query += " AND s.service_type = %s"
                params.append(selected_service_type)

            # Filter by contractor ID if provided
            if contractor_id:
                query += " AND sa.contractor_id = %s"
                params.append(contractor_id)

            # Order the results by date
            query += " ORDER BY sa.date DESC"
            cursor.execute(query, params)
            records = cursor.fetchall()

            # Fetch distinct years for the year filter
            cursor.execute("SELECT DISTINCT YEAR(date) as year FROM services_availed ORDER BY year DESC")
            years = [row['year'] for row in cursor.fetchall()]

    finally:
        connection.close()

    return render_template(
        'ServicesAvailed.html',
        records=records,
        years=years,
        service_types=service_types,
        selected_year=selected_year,
        selected_service_type=selected_service_type,
        contractor_id=contractor_id
    )

@app.route('/services-availed-input', methods=['GET', 'POST'])
def services_availed_input():
    if request.method == 'POST':
        # Handle form submission
        customer_id = request.form.get('customer_id')
        meter_id = request.form.get('meter_id')
        service_id = request.form.get('service_id')
        contractor_id = request.form.get('contractor_id')
        date = request.form.get('date')

        connection = connect_to_db()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Insert into services_availed table
                query = """
                    INSERT INTO services_availed (
                        transaction_id,
                        customer_id,
                        meter_id,
                        service_id,
                        contractor_id,
                        date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                # Generate a unique transaction_id
                cursor.execute("SELECT MAX(transaction_id) AS max_transaction_id FROM services_availed")
                max_transaction_id = cursor.fetchone()
                if max_transaction_id and max_transaction_id['max_transaction_id']:
                    transaction_id = f"SER{int(max_transaction_id['max_transaction_id'][3:]) + 1:05}"
                else:
                    transaction_id = "SER00001"

                cursor.execute(query, (transaction_id, customer_id, meter_id, service_id, contractor_id, date))

                # Fetch the service type
                cursor.execute("SELECT service_type FROM services WHERE service_id = %s", (service_id,))
                service_type = cursor.fetchone()
                if service_type:
                    service_type = service_type['service_type']
                    print(f"Service Type: {service_type}")

                # Update the meter's status
                new_status = None
                if service_type == 'Disconnection':
                    new_status = 'disconnected'
                elif service_type == 'Reconnection':
                    new_status = 'connected'
                elif service_type == 'Removal':
                    new_status = 'removed'

                if new_status:
                    print(f"Updating Meter ID {meter_id} to status: {new_status}")
                    try:
                        # Update the meter's status
                        cursor.execute(
                            "UPDATE meters SET status = %s WHERE meter_id = %s",
                            (new_status, meter_id)
                        )

                        # Check if the update was successful
                        affected_rows = cursor.rowcount
                        print(f"Rows affected by the update: {affected_rows}")

                        # Fetch the updated status for verification
                        cursor.execute("SELECT status FROM meters WHERE meter_id = %s", (meter_id,))
                        updated_status = cursor.fetchone()
                        if updated_status:
                            print(f"Updated Status in DB: {updated_status['status']}")
                        else:
                            print("No rows found for the given Meter ID.")
                    except Exception as e:
                        print(f"Error updating meter status: {e}")
                        raise


            connection.commit()
            print("Meter status update committed.")
            return redirect('/services-availed')
        except Exception as e:
            print(f"Error processing service availed: {e}")
            connection.rollback()
            return f"Failed to process service availed: {e}", 500

    # For GET method, render the form
    else:
        connection = connect_to_db()
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Fetch customers
                cursor.execute("SELECT customer_id, CONCAT(first_name, ' ', last_name) AS customer_name FROM customers")
                customers = cursor.fetchall()

                # Fetch services sorted by service ID
                cursor.execute("SELECT service_id, service_type AS service_name FROM services ORDER BY service_id")
                services = cursor.fetchall()

                # Fetch contractors (initially empty, will be filtered dynamically)
                cursor.execute("""
                    SELECT 
                        contractor_id, 
                        CONCAT(first_name, ' ', last_name) AS contractor_name, 
                        job_title 
                    FROM contractors 
                    WHERE status = 'active' 
                    ORDER BY contractor_id
                """)
                contractors = cursor.fetchall()

                # Fetch all meters (initially empty, will be filtered dynamically)
                cursor.execute("""
                    SELECT meter_id, account_number 
                    FROM meters 
                    WHERE status = 'connected' 
                    ORDER BY meter_id
                """)
                meters = cursor.fetchall()

        finally:
            connection.close()

        return render_template(
            'ServicesAvailedInput.html',
            customers=customers,
            services=services,
            contractors=contractors,
            meters=meters
        )

@app.route('/get-meters', methods=['GET'])
def get_meters():
    customer_id = request.args.get('customer_id')
    connection = connect_to_db()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch meters connected to the given customer ID and filter out 'removed'
            query = """
                SELECT m.meter_id, m.account_number
                FROM meters m
                WHERE m.customer_id = %s AND m.status IN ('connected', 'disconnected')
                ORDER BY m.meter_id
            """
            cursor.execute(query, (customer_id,))
            meters = cursor.fetchall()
            return {"meters": meters}
    except Exception as e:
        print(f"Error fetching meters: {e}")
        return {"meters": []}, 500
    finally:
        connection.close()

@app.route('/get-contractors', methods=['GET'])
def get_contractors():
    service_id = request.args.get('service_id')
    connection = connect_to_db()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch contractors connected to the given service ID
            query = """
                SELECT 
                    contractor_id, 
                    CONCAT(first_name, ' ', last_name) AS contractor_name,
                    job_title
                FROM contractors
                WHERE service_id = %s AND status = 'active'
                ORDER BY contractor_id
            """
            cursor.execute(query, (service_id,))
            contractors = cursor.fetchall()
            return {"contractors": contractors}
    except Exception as e:
        print(f"Error fetching contractors: {e}")
        return {"contractors": []}, 500
    finally:
        connection.close()

@app.route('/get-services', methods=['GET'])
def get_services():
    meter_id = request.args.get('meter_id')

    connection = connect_to_db()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch the meter's status
            cursor.execute("SELECT status FROM meters WHERE meter_id = %s", (meter_id,))
            meter = cursor.fetchone()
            if not meter:
                return {"services": []}, 404  # No meter found

            meter_status = meter['status']

            # Determine valid services based on meter status
            if meter_status == 'connected':
                # Allow everything except 'installation' and 'reconnection'
                cursor.execute("""
                    SELECT service_id, service_type AS service_name 
                    FROM services 
                    WHERE service_type NOT IN ('installation', 'reconnection')
                    ORDER BY service_id
                """)
            elif meter_status == 'disconnected':
                # Allow everything except 'installation' and 'disconnection'
                cursor.execute("""
                    SELECT service_id, service_type AS service_name 
                    FROM services 
                    WHERE service_type NOT IN ('installation', 'disconnection')
                    ORDER BY service_id
                """)
            else:
                # No valid services for other statuses
                cursor.execute("""
                    SELECT service_id, service_type AS service_name 
                    FROM services 
                    WHERE service_type NOT IN ('installation')
                    ORDER BY service_id
                """)

            services = cursor.fetchall()
            return {"services": services}

    except Exception as e:
        print(f"Error fetching services: {e}")
        return {"services": []}, 500
    finally:
        connection.close()

@app.route('/services-availed-install', methods=['GET'])
def services_availed_install():
    connection = connect_to_db()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT customer_id, CONCAT(first_name, ' ', last_name) AS customer_name FROM customers")
            customers = cursor.fetchall()

            cursor.execute("""
                SELECT contractor_id, last_name, first_name, contact_number
                FROM contractors
                WHERE service_id = '00001'
            """)
            contractors = cursor.fetchall()

    finally:
        connection.close()

    return render_template('ServicesAvailedInstall.html', customers=customers, contractors=contractors)

@app.route('/add-meter', methods=['POST'])
def add_meter():
    customer_id = request.form.get('customer_id')
    address_details = request.form.get('address_details')
    barangay = request.form.get('barangay')
    city = request.form.get('city')
    postal_code = request.form.get('postal_code')
    account_number = helper.generate_account_number()
    contractor_id = request.form.get('contractor_id')

    connection = connect_to_db()
    try:
        with connection.cursor() as cursor:
            # Check if the account number is unique
            cursor.execute("SELECT COUNT(*) FROM meters WHERE account_number = %s", (account_number,))
            while cursor.fetchone()[0] > 0:
                account_number = helper.generate_account_number()

            # Generate a unique address_id
            cursor.execute("SELECT MAX(address_id) FROM addresses")
            max_address_id = cursor.fetchone()[0]
            if max_address_id is None:
                address_id = "00001"
            else:
                address_id = f"{int(max_address_id) + 1:05}"

            # Insert into addresses table
            address_query = """
                INSERT INTO addresses (
                    address_id, address_details, barangay, city, postal_code
                )
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(address_query, (address_id, address_details, barangay, city, postal_code))

            # Generate a unique meter_id
            cursor.execute("SELECT MAX(meter_id) FROM meters")
            max_meter_id = cursor.fetchone()[0]
            if max_meter_id is None:
                meter_id = "00001"
            else:
                meter_id = f"{int(max_meter_id) + 1:05}"

            # Insert into meters table
            meter_query = """
                INSERT INTO meters (
                    meter_id, customer_id, install_address, account_number, installation_date, status
                )
                VALUES (%s, %s, %s, %s, CURDATE(), 'connected')
            """
            cursor.execute(meter_query, (meter_id, customer_id, address_id, account_number))

            # Insert new service_availed row
            new_serv_id = helper.generateID(cursor, "services_availed", "transaction_id", "SER")
            # Insert into meters table
            service_query = """
                INSERT INTO services_availed (
                    transaction_id, customer_id, meter_id, service_id, contractor_id, date
                )
                VALUES (%s, %s, %s, %s, %s, CURDATE())
            """
            cursor.execute(service_query, (new_serv_id, customer_id, meter_id, "00001", contractor_id))

        connection.commit()
        return redirect('/services-availed')
    except Exception as e:
        print(f"Error adding meter: {e}")
        connection.rollback()
        return f"Failed to install meter: {e}", 500
    finally:
        connection.close()

@app.route('/bill-generation', methods=['GET'])
def bill_generation():
    # Get filter parameters from the URL
    due_date = request.args.get('due_date')
    status = request.args.get('status')
    account_number = request.args.get('account_number')

    # Connect to the database
    connection = connect_to_db()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Base query
            query = """
                SELECT 
                    b.billing_id,
                    m.account_number,
                    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
                    b.consumption_fee,
                    b.service_fee,
                    b.total_amount,
                    b.start_date,
                    b.end_date,
                    b.consumption,
                    DATE_FORMAT(b.due_date, '%Y-%m-%d') AS due_date,
                    b.payment_status
                FROM billings b
                JOIN meters m ON b.meter_id = m.meter_id
                JOIN customers c ON m.customer_id = c.customer_id
                WHERE 1=1
            """

            # Apply filters based on query parameters

            # Filter by due date (if specified)
            if due_date:
                query += " AND DATE_FORMAT(b.due_date, '%Y-%m-%d') = %s"
            
            # Filter by payment status (if specified)
            if status:
                query += " AND b.payment_status = %s"
            
            # Filter by account number (if specified)
            if account_number:
                query += " AND m.account_number LIKE %s"
            
            query += " ORDER BY b.due_date DESC"

            # Prepare the query parameters for safe insertion
            params = []
            if due_date:
                params.append(due_date)
            if status:
                params.append(status)
            if account_number:
                params.append(f'%{account_number}%')

            # Execute the query with filters
            cursor.execute(query, tuple(params))
            bills = cursor.fetchall()

    finally:
        connection.close()

    # Get the years for the year filter dropdown
    years = get_available_years()

    return render_template(
        'BillGeneration.html',
        bills=bills,
        years=years,
        selected_due_date=due_date,
        selected_status=status,
        selected_account_number=account_number
    )

def get_available_years():
    connection = connect_to_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT YEAR(b.due_date) AS year
                FROM billings b
                ORDER BY year DESC
            """)
            years = cursor.fetchall()
            return years
    finally:
        connection.close()

# Route: Bill Input Page
@app.route('/bill-input', methods=['GET'])
def bill_input():
    connection = connect_to_db()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Fetch all meter and account numbers
            query = """
                SELECT 
                    m.meter_id, 
                    m.account_number 
                FROM meters m
                WHERE m.status = 'connected'
            """
            cursor.execute(query)
            meters = cursor.fetchall()
    finally:
        connection.close()

    return render_template('BillInput.html', meters=meters)


# Route: Generate Bill (POST)
@app.route('/generate-bill', methods=['POST'])
def generate_bill():
    bill_start = request.form.get('bill_start')
    bill_end = request.form.get('bill_end')
    due_date = request.form.get('due_date')
    consumptions = request.form.to_dict(flat=False)  # Get all form data

    connection = connect_to_db()
    try:
        with connection.cursor() as cursor:
            for key, consumption_list in consumptions.items():
                if not key.startswith('consumption['):
                    continue

                # Extract meter_id
                meter_id = key[12:-1]  # Strip 'consumption[' and ']'
                consumption = consumption_list[0]

                # Validate data
                if not meter_id.isnumeric() or not consumption.isnumeric():
                    print(f"Invalid data for Meter ID: {meter_id}. Skipping.")
                    continue

                consumption = float(consumption)
                print(f"Processing Meter ID: {meter_id}, Consumption: {consumption} kWh")

                # Generate a new billing_id
                cursor.execute("SELECT MAX(billing_id) FROM billings")
                max_billing_id = cursor.fetchone()[0]
                if max_billing_id is None:
                    billing_id = "BIL001"
                else:
                    billing_id = f"BIL{int(max_billing_id[3:]) + 1:03}"

                print(f"Generated Billing ID: {billing_id}")

                # Insert the bill
                query = """
                    INSERT INTO billings (
                        billing_id,
                        meter_id,
                        consumption_fee,
                        total_amount,
                        start_date,
                        end_date,
                        due_date,
                        payment_status,
                        consumption
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Unpaid', %s)
                """
                consumption_fee = consumption * 12  # Assuming 12 pesos/kWh
                total_amount = consumption_fee  # Add other fees if necessary

                params = (
                    billing_id,
                    meter_id,
                    consumption_fee,
                    total_amount,
                    bill_start,
                    bill_end,
                    due_date,
                    consumption,  # Add consumption value
                )

                print(f"Executing Query: {query}")
                print(f"With Parameters: {params}")

                try:
                    cursor.execute(query, params)
                    print(f"Successfully executed for Meter ID: {meter_id}")
                except Exception as e:
                    print(f"Error executing query for Meter ID: {meter_id}. Error: {e}")

        # Commit the transaction
        connection.commit()
        print("Bills successfully generated and committed to the database.")

    except Exception as e:
        print(f"Error occurred during bill generation: {e}")
        connection.rollback()

    finally:
        connection.close()

    return redirect('/bill-generation')

if __name__ == '__main__':
    app.run(debug=True)