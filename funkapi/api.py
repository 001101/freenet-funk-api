import requests
import boto3
from warrant.aws_srp import AWSSRP


class FunkAPI:
    API_ENDPOINT = "https://appapi.funk.services/"
    API_KEY = "FZ3OkFFfdMahh4a1xagOnaon39pUpml732kkb2Aw"
    AWS_REGION = "eu-central-1"
    AWS_POOL_ID = "eu-central-1_ZPDpzBJy4"
    AWS_CLIENT_ID = "3asd34f9vfrg6pd2mrbqhn3g3r"

    def __init__(self, username, password, token=None, always_test_token=False):
        self.username = username
        self.password = password
        self.always_test_token = always_test_token

        self.client = boto3.client('cognito-idp', region_name=self.AWS_REGION, aws_access_key_id="",
                                   aws_secret_access_key="")

        self.aws = AWSSRP(username=self.username, password=self.password,
                          pool_id=self.AWS_POOL_ID,
                          client_id=self.AWS_CLIENT_ID, client=self.client)

        self.token = None
        self.getToken(token=token)

        self.data = None
        self.getData()

    # TOKEN
    def getToken(self, refresh=False, token=None):
        if token is not None:
            if self.testToken(token):
                self.token = token
                return self.token
            self.getToken(refresh=True)

        if self.token is None or refresh or (
                False if not self.always_test_token else not self.testToken(self.token)):
            self.token = self.aws.authenticate_user(
            )["AuthenticationResult"]["AccessToken"]
        return self.token

    def testToken(self, token):
        if token is None:
            return False

        json = {"operationName": "CustomerForDashboardQuery", "variables": {},
                "query": "query CustomerForDashboardQuery { me { id } }"}

        req = requests.post(self.API_ENDPOINT, json=json,
                            headers={
                                "x-api-key": self.API_KEY,
                                "Authorization": "Bearer " + token
                            })
        result = req.json()

        if "errors" in result.keys():
            return False
        return True

    # DATA
    def getData(self, refresh=False):
        json = {"operationName": "CustomerForDashboardQuery", "variables": {},
                "query": "query CustomerForDashboardQuery {\n  me {\n    ...CustomerForDashboardFragment\n    __typename\n  }\n}\n\nfragment CustomerForDashboardFragment on Customer {\n  id\n  details {\n    ...DetailsFragment\n    __typename\n  }\n  customerProducts {\n    ...ProductFragment\n    __typename\n  }\n  __typename\n}\n\nfragment DetailsFragment on Details {\n  firstName\n  lastName\n  dateOfBirth\n  contactEmail\n  __typename\n}\n\nfragment ProductFragment on FUNKCustomerProduct {\n  id\n  state\n  paymentMethods {\n    ...PaymentMethodFragment\n    __typename\n  }\n  mobileNumbers {\n    ...MobileNumberFragment\n    __typename\n  }\n  sims {\n    ...SIMFragment\n    __typename\n  }\n  plans: planCustomerProductServices {\n    ...PlanFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PaymentMethodFragment on PaymentMethod {\n  id\n  state\n  approvalChallenge {\n    approvalURL\n    __typename\n  }\n  agreement {\n    state\n    payerInfo {\n      payerID\n      email\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MobileNumberFragment on MobileNumberCPS {\n  id\n  number\n  state\n  usage {\n    usedDataPercentage\n    __typename\n  }\n  productServiceId\n  productServiceInfo {\n    id\n    label\n    __typename\n  }\n  ... on MNPImportCustomerProductService {\n    otherProviderShortcut\n    otherProviderCustomName\n    otherContract {\n      contractType\n      mobileNumber\n      mobileNumberIsVerified\n      __typename\n    }\n    mnpInfos {\n      confirmedPortingDate\n      lastPortingResult\n      problemCode\n      problemReason\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SIMFragment on SIMCustomerProductService {\n  id\n  networkState\n  state\n  iccid\n  delivery {\n    state\n    trackingDetails {\n      stateId\n      stateLabel\n      trackingURL\n      __typename\n    }\n    deliveryProvider\n    address {\n      city\n      additionalInfo\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PlanFragment on PlanCustomerProductService {\n  id\n  booked\n  starts\n  state\n  productServiceId\n  productServiceInfo {\n    id\n    label\n    follower {\n      id\n      label\n      __typename\n    }\n    marketingInfo {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"}

        if self.data is None or refresh:
            req = requests.post(self.API_ENDPOINT, json=json,
                                headers={
                                    "x-api-key": self.API_KEY,
                                    "Authorization": "Bearer " + self.getToken()
                                })

            self.data = req.json()

        return self.data

    def getPersonalInfo(self, refreshData=False):
        data = self.getData(refresh=refreshData)["data"]["me"]
        personalInfo = {"id": data["id"], **data["details"]}
        del personalInfo["__typename"]
        return personalInfo

    def getOrderedProducts(self, refreshData=False):
        return self.getData(refresh=refreshData)["data"]["me"]["customerProducts"]

    def getCurrentPlan(self, refreshData=False):
        return self.getData(refresh=refreshData)["data"]["me"]["customerProducts"][0]["plans"][-1]

    # TARIFFS
    def orderPlan(self, planID, productID=None, refreshData=True):
        if productID is None:
            productID = self.getOrderedProducts()[0]["id"]

        json = {"operationName": "AddPlanToProductMutation",
                "variables": {"productID": productID, "planID": str(planID)},
                "query": "mutation AddPlanToProductMutation($productID: String!, $planID: String!) {\n  planAddToCustomerProduct(customerProductId: $productID, productServiceId: $planID) {\n    ...PlanFragment\n    __typename\n  }\n}\n\nfragment PlanFragment on PlanCustomerProductService {\n  id\n  booked\n  starts\n  state\n  productServiceId\n  productServiceInfo {\n    id\n    label\n    follower {\n      id\n      label\n      __typename\n    }\n    marketingInfo {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"}

        req = requests.post(self.API_ENDPOINT, json=json,
                            headers={
                                "x-api-key": self.API_KEY,
                                "Authorization": "Bearer " + self.getToken()
                            })

        self.getData(refresh=refreshData)

        return req.json()

    def removeProduct(self, personalPlanID, refreshData=True):

        json = {"operationName": "TerminatePlanMutation",
                "variables": {"planID": personalPlanID},
                "query": "mutation TerminatePlanMutation($planID: String!) {\n  planTerminate(customerProductServiceId: $planID) {\n    ...PlanFragment\n    __typename\n  }\n}\n\nfragment PlanFragment on PlanCustomerProductService {\n  id\n  booked\n  starts\n  state\n  productServiceId\n  productServiceInfo {\n    id\n    label\n    follower {\n      id\n      label\n      __typename\n    }\n    marketingInfo {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"}

        req = requests.post(self.API_ENDPOINT, json=json,
                            headers={
                                "x-api-key": self.API_KEY,
                                "Authorization": "Bearer " + self.getToken()
                            })

        self.getData(refresh=refreshData)

        return req.json()

    def order1GBPlan(self, **kwargs):
        return self.orderPlan(9, **kwargs)

    def orderUnlimitedPlan(self, **kwargs):
        return self.orderPlan(8, **kwargs)

    def startPause(self, **kwargs):
        return self.orderPlan(42, **kwargs)

    def stopLatestPlan(self, productIndex=0, **kwargs):
        personalPlanID = self.getOrderedProducts(
        )[productIndex]["plans"][-1]["id"]
        self.removeProduct(personalPlanID, **kwargs)
