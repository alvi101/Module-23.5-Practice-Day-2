from django import forms
from .models import Transaction, BankStatus
from accounts.models import UserBankAccount

# return bankrup valus of one object from BankStatus model


def check_bank_status():
    bank_status = BankStatus.objects.get()
    return bank_status.bankrupt


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')  # account value ke pop kore anlam
        super().__init__(*args, **kwargs)
        # ei field disable thakbe
        self.fields['transaction_type'].disabled = True
        # user er theke hide kora thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput()

        # store bankrupt status when initializing
        self.bank_status = check_bank_status()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):
    def clean_amount(self):  # amount field ke filter korbo
        min_deposit_amount = 100
        # user er fill up kora form theke amra amount field er value ke niye aslam, 50
        amount = self.cleaned_data.get('amount')
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance  # 1000
        amount = self.cleaned_data.get('amount')

        # first check if bank is banktup or not
        if self.bank_status:
            raise forms.ValidationError(
                f'Cannot withdraw. Bank is bankrupt'
            )

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance:  # amount = 5000, tar balance ache 200
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount


class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount


# Practice day codes:


class TransferMoneyForm(TransactionForm):
    account_no = forms.IntegerField()

    class Meta(TransactionForm.Meta):
        model = Transaction
        fields = [
            'amount',
            'transaction_type',
            'account_no',
        ]

    def clean_amount(self):
        transfer_amount = self.cleaned_data.get('amount')
        account = self.account

        if transfer_amount > account.balance:
            raise forms.ValidationError(
                f'You do not have sufficient balance'
            )

        return transfer_amount

    # https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist-in-django

    def clean_account_no(self):
        account_no = self.cleaned_data.get('account_no')

        try:
            reciever = UserBankAccount.objects.get(account_no=account_no)
        except UserBankAccount.DoesNotExist:
            reciever = None

        if reciever == None:
            raise forms.ValidationError(
                f'Account does not exist'
            )

        return account_no
