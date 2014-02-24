-- Some testing data to fill up the pyoseo database while testing

INSERT INTO product (id, short_name)
VALUES
(1, 'LST'),
(2, 'LST10');

-------------------
INSERT INTO 'option' (id, name, type_, option_type)
VALUES
(1, 'dataset', 'str', 'product_option'),
(2, 'file_format', 'str', NULL);

-------------------
INSERT INTO product_option (id, product_id)
VALUES
(1, 1);

-------------------
INSERT INTO option_choice (id, option_id, value)
VALUES
(1, 1, 'LST'),
(2, 1, 'Q_FLAGS'),
(3, 1, 'errorbar_LST'),
(4, 2, 'HDF5'),
(5, 2, 'netCDF'),
(6, 2, 'GeoTiff');

-------------------
INSERT INTO customizable_item (id)
VALUES
(1),
(2),
(3),
(4),
(5);

-------------------
INSERT INTO selected_option (id, option_id, customizable_item_id, value)
VALUES
(1, 1, 1, 'LST'),
(2, 1, 1, 'Q_FLAGS'),
(3, 2, 1, 'netCDF');

-------------------
INSERT INTO 'user' ('admin', name, e_mail, full_name, password)
VALUES 
(1, 'ricardogsilva', 'ricardo.silva@ipma.pt', 'Ricardo Garcia Silva', 'pyoseo'),
(0, 'jmacedo', 'joao.macedo@ipma.pt', 'Joao Macedo', 'pyoseo'),
(0, 'scoelho', 'sandra.coelho@ipma.pt', 'Sandra Coelho', 'pyoseo');

-------------------
INSERT INTO 'order' (status, created_on, status_changed_on, reference, remark,
                     packaging, priority, order_type, additional_status_info,
                     mission_specific_status_info)
VALUES 
('Submitted', datetime(), datetime(), NULL, NULL, 'bzip2', 'STANDARD',
'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', NULL, NULL),
('Submitted', datetime(), datetime(), 'a sample reference', 'a sample remark',
'bzip2', 'STANDARD', 'normal_order', 'some additional status information',
'some mission specific status information');

-------------------
INSERT INTO 'delivery_address' (first_name, last_name, company_ref,
                                street_address, city, state,
                                postal_code, country, post_box,
                                telephone_number, fax, delivery_address_type)
VALUES
('John', 'Doe', 'stuff inc.', 'da street', 'mira city', 'setubal', '2800',
    'Portugal', NULL, '212212211', NULL, 'delivery_information'),
(NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    'delivery_information'),
('John', 'Doe', 'stuff inc.', 'da street', 'mira city', 'setubal', '2800',
    'Portugal', NULL, '212212211', NULL, 'invoice_address');

-------------------
INSERT INTO 'delivery_information' (id, order_id)
VALUES
(1, 3),
(2, 4);

-------------------
INSERT INTO 'invoice_address' (id, order_id)
VALUES
(3, 3);
-------------------
INSERT INTO 'online_address' (delivery_information_id, protocol,
                              server_address)
VALUES
(2, 'ftp', 'saf1000.meteo.pt');

-------------------
INSERT INTO 'normal_order' (id, user_id)
VALUES
(1, 1),
(2, 1),
(3, 1),
(4, 2),
(5, 2);

-------------------
INSERT INTO 'order_item' (order_id, catalog_id)
VALUES 
(1, '12345'),
(1, '12346'),
(1, '12347'),
(1, '12348'),
(1, '12349'),
(1, '12350'),
(2, '12345'),
(2, '12346'),
(2, '12352'),
(2, '12353'),
(2, '12354');
