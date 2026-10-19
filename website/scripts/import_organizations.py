#! /usr/bin/python
import json
from pathlib import Path

from website.models import CPEProduct, CPEVendor, Organization, Product
from website.web.bootstrap import db


def import_organizations(file_path: str, user_id: int) -> None:
    """Imports a list of organizations from a JSON file."""
    with open(Path(file_path)) as json_file:
        organizations = json.loads(json_file.read())
        for organization in organizations:
            if "uuid" in organization:
                new_organization = Organization(
                    name=organization["name"],
                    short_name=organization["name"],
                    owner_id=user_id,
                    uuid=organization["uuid"],
                )
            else:
                new_organization = Organization(
                    name=organization["name"],
                    short_name=organization["name"],
                    owner_id=user_id,
                )
            db.session.add(new_organization)
            db.session.commit()
            for cpe in organization["cpe_vendor_names"]:
                new_cpe_vendor = CPEVendor(
                    name=cpe, organization_id=new_organization.id
                )
                db.session.add(new_cpe_vendor)
                db.session.commit()

            for product in organization["products"]:
                new_product = Product(
                    name=product["name"],
                    short_name=product["name"],
                    submitter_id=user_id,
                )
                db.session.add(new_product)
                db.session.commit()

                new_organization.products.append(new_product)
                db.session.commit()

                for cpe in product["cpe_product_names"]:
                    new_cpe_product = CPEProduct(name=cpe, product_id=new_product.id)
                    db.session.add(new_cpe_product)
                    db.session.commit()
